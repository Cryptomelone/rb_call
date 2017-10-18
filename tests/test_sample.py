import unittest
import rb_call


class TestSample(unittest.TestCase):
    def setUp(self):
        self.client = rb_call.RubySession()

    def test_one(self):
        self.client.require("json")  # `require "json"`
        json = self.client.const('JSON')  # get JSON class (This is a Ruby class.)
        print(json.dump(['foo', 'bar', 'baz']))  # call method against JSON class

        dirg = self.client.const('Dir')  # get another class `Dir`
        for f in dirg.glob('*'):  # iterate over an object of Ruby
            print(f)  # Array of Ruby is mapped to list of Python

        json_string = '{"a": 1, "b":2, "c":3}'
        parsed = json.load(json_string)  # parse JSON string using Ruby's JSON
        for k, v in parsed.items():  # Hash of Ruby is mapped to dict of Python
            print(k, v)

        self.client.require_relative('sample_class')  # load a Ruby library 'sample_class.rb'
        my_class = self.client.const('MyClass')  # get a Class defined in 'sample_class.rb'
        obj = my_class('a')  # create an instance of MyClass
        print(obj, repr(obj))  # when printing a Ruby object, `to_s` method is called
        print(obj.inspect())  # all Ruby methods are available.
        print(dir(obj))  # dir invokes `public_methods` in Ruby
        print(obj.m1(), obj.m2(1, 2), obj.m3(3, b=4))
        # You can call Ruby methods with args. Keyword arguments are also available.

        proc = obj.m4('arg of proc')  # a Ruby method that returns a Proc
        print("proc:", proc())  # calling proc

        try:
            obj.m2()  # when an exception happens in Ruby, RubyException is raised
        except rb_call.RubyException as ex:
            print(ex.args, repr(ex.rb_exception))  # ex.args has a message from the exception object in Ruby.

        d = my_class.cm5()  # Hash and Array in Ruby correspond to Dictionary and List in Python
        print(d)  # => {1: RubyObject, 2: [1, RubyObject]}

        e = my_class.cm6()  # Not only simple Array but an Enumerator is also supported
        for i in e:  # You can iterate using `for` syntax over an Enumerable
            print(i)

        obj2 = my_class.cm7(obj)  # you can pass a RubyObject as an argument
        print(obj2 == obj)  # If two objects refers to the same objects, they are regarded as same.
