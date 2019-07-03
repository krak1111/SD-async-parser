def writable_method(func):
    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)
        print(f'I say {self.test}')
        return True
    return wrapper
    
class Test_class(object):
    """docstring for Test_class"""
    def __init__(self):
        print("Test for deco")
        self.test = 'Hello'

    @writable_method
    def test_func(self):
        print('Testing')


if __name__ == '__main__':
    h = Test_class()

    h.test_func()