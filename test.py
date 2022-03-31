import logging

class Test:
	logger = logging.getLogger("Test")
	logger.setLevel(logging.DEBUG)
	fh = logging.FileHandler('test.log')
	formatter = logging.Formatter('%(asctime)s | %(name)s | [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
	fh.setFormatter(formatter)
	logger.addHandler(fh)

	def __init__(self):
		pass


test = Test()

print(test.logger)
print(Test.logger)
print(test.logger is Test.logger)