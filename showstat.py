##
#   showstat.py
#   Shows disk information for a V9k hard disk image (linear)
#
#   Copyright (c) Daniel Jameson 2025
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import click

@click.command()
@click.argument("hdfile", type=click.File("rb"))
def cli(hdfile):
    """This command shows the disk label for a Victor 9000 Hard Disk image file"""

    click.echo("Hello!")

if __name__ == "__main__":
        cli()
