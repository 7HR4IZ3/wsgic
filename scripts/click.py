import click

class Script:
	def __init__(self):
		self.__group = click.group()
		self.option = click.option
	
	def __call__(self):
		return click.command()

@click.group()
@click.option("--name", default="Thraize")
def main(name):
	print(name)

main()