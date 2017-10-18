import subprocess
import os
import inspect
import atexit
import msgpack
import msgpackrpc


class RubyObject:
    session = None

    @staticmethod
    def cast(obj):
        if isinstance(obj, msgpack.ExtType):
            assert obj.code == 40
            rb_class, obj_id = msgpack.unpackb(obj.data, encoding='utf-8')
            return RubyObject(rb_class, obj_id)
        elif isinstance(obj, list):
            return [RubyObject.cast(x) for x in obj]
        elif isinstance(obj, dict):
            return {k: RubyObject.cast(v) for k, v in obj.items()}
        elif isinstance(obj, bytes):
            return obj.decode('utf-8')
        else:
            return obj

    def __init__(self, rb_class, obj_id):
        self.rb_class = rb_class
        self.obj_id = obj_id

    def __del__(self):
        if self.session:
            self.session.del_object(self.obj_id)

    def __eq__(self, other):
        return self.send('==', other)

    def __dir__(self):
        return self.send('public_methods')

    def __iter__(self):
        return self.send("each")

    def __str__(self):
        return self.send('to_s')

    def __repr__(self):
        return self.send('inspect')

    def __len__(self):
        return self.send("size")

    def __getattr__(self, attr):
        def _method_missing(*args, **kwargs):
            return self.send(attr, *args, **kwargs)

        return _method_missing

    def __getitem__(self, index):
        return self.send('[]', index)

    def send(self, method, *args, **kwargs):
        try:
            obj = self.session.client.call('send_method', self.obj_id, method, args, kwargs)
            return self.cast(obj)
        except msgpackrpc.error.RPCError as ex:
            arg = RubyObject.cast(ex.args[0])
            if isinstance(arg, RubyObject):
                raise RubyException(arg.message(), arg) from None
            else:
                raise

    # msgpack-rpc-python uses `to_msgpack` method
    def to_msgpack(self):
        return msgpack.ExtType(40, msgpack.packb([self.rb_class, self.obj_id]))

    def __next__(self):
        try:
            return self.send("next")
        except RubyException as ex:
            if ex.rb_exception.rb_class == 'StopIteration':
                raise StopIteration()
            else:
                raise

    def __call__(self, *args, **kwargs):
        if self.rb_class == 'Class':
            return self.send('new', *args, **kwargs)
        else:
            return self.send('call', *args, **kwargs)


class RubyException(Exception):
    def __init__(self, message, rb_exception):
        self.args = (message,)
        self.rb_exception = rb_exception


class RubySession:
    def __init__(self):
        server_rb = os.path.abspath(os.path.join(os.path.dirname(__file__), 'rb_call_server.rb'))

        def setpgrp():
            os.setpgrp()

        self.proc = subprocess.Popen(['ruby', server_rb], stdout=subprocess.PIPE, preexec_fn=setpgrp)

        def cleanup():
            RubyObject.session = None
            self.proc.terminate()

        atexit.register(cleanup)
        port = int(self.proc.stdout.readline())
        self.proc.stdout.close()
        self.address = msgpackrpc.Address("localhost", port)
        self.client = msgpackrpc.Client(self.address, unpack_encoding='utf-8')
        RubyObject.session = self
        self.kernel = RubyObject.cast(self.client.call('get_kernel'))

    def del_object(self, obj_id):
        return self.client.call('del_object', obj_id)

    def send_kernel(self, method, *args, **kwargs):
        return self.kernel.send(method, *args, **kwargs)

    def require(self, arg):
        return self.send_kernel('require', arg)

    def require_relative(self, arg):
        caller_path = inspect.stack()[1][1]
        abspath = os.path.abspath(os.path.join(os.path.dirname(caller_path), arg))
        return self.send_kernel('require_relative', abspath)

    def const(self, const_name):
        obj = self.send_kernel("const_get", const_name)
        return RubyObject.cast(obj)
