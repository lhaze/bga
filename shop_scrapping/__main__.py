import click
from python_path import PythonPath

with PythonPath("..", relative_to=__file__):
    from shop_scrapping.process import (
        build_scrappers,
        load_config,
        process_scrappers,
    )


@click.command()
@click.argument('config_file', envvar='BGA_SHOP_CONFIG', type=click.File('r'))
def main(config_file):
    config = load_config(config_file)
    spiders = build_scrappers(config)
    process_scrappers(spiders)


if __name__ == '__main__':
    main()
