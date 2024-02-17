# TODO: merge all these small files into one, ship with genkey
# TODO: write readme.md explaining how to use

# Run telex-converter to process and get 20 txt files in telex
# Import convert_multiple_lines_to_telex, get list of 20 files as output
# Note that 20 files actually were created
# Run genkey-runner to get json files from genkey

# Run corpus-json-combiner to combine all those json files into one big file, this is the main corpus.json

# Run extracter to see relevant stats

# Delete files created by other modules

import shutil
import sys
from pathlib import Path

import click

from .util import create_section_separator, create_sub_section_separator

from .genkey_runner import genkey_runner as gr
from .json_combiner import combine as jc
from .telex_converter import telexify as tc

MAPPING_PATH = Path(
    "./src/converter/telex_converter/new_telex_mapping-w.json"
).resolve()
DATA_PATH = Path("./data")

GENKEY_FOLDER_PATH = Path("./src/converter/genkey_runner/genkey").resolve()


@click.group()
def cli():
    pass


@cli.command()
@click.argument("filename", type=click.Path(exists=True))
@click.option(
    "--limit",
    "-l",
    default=10000,
    help="Limit the number of lines processed, in case you have a very big input file",
)
@click.option(
    "--name",
    "-n",
    prompt=True,
    required=True,
    type=str,
    help="Give this text a name so you can look up its stats later.",
)
def load(filename: str, limit: int, name: str):
    """Load, convert vietnamese text and spit out key usage."""

    # Load telex mapping
    telex_mapping = tc.load_telex_mapping(MAPPING_PATH)
    if not tc.validate_telex_mapping(telex_mapping):
        sys.exit("telex mapping contains invalid info")

    # Check output path
    output_path = DATA_PATH / name
    while output_path.exists():
        is_confirmed = click.confirm(
            f"{name} is already used. Are you sure you want to overwrite?"
        )
        if not is_confirmed:
            name = click.prompt("Name")
            output_path = DATA_PATH / name
        else:
            break

    # Put all tmp files in one folder for easy clean up
    tmp_dir_path = output_path / "tmp"
    Path.mkdir(tmp_dir_path, parents=True, exist_ok=True)

    create_section_separator()
    click.echo("Converting texts into telex input...")
    output_count = tc.convert_and_save(filename, telex_mapping, limit, tmp_dir_path)

    create_sub_section_separator()
    if output_count == 0:
        click.echo("No file created. Something went wrong.")
    else:
        click.echo(
            f"{output_count} files created successfully. Output written to {tmp_dir_path}."
        )

    # Run genkey
    create_section_separator()
    click.echo("Analyzing telex input files with genkey...")

    if not gr.check_genkey_exist(GENKEY_FOLDER_PATH):
        sys.exit("Cannot find genkey executable.")
    gr_file_list = gr.get_input_file_list(tmp_dir_path)
    gr_output_path = gr.create_output_dir(tmp_dir_path)
    gr_output_files = gr.run_genkey(gr_file_list, gr_output_path, GENKEY_FOLDER_PATH)
    create_sub_section_separator()
    click.echo(
        f"{len(gr_output_files) } files analyzed with genkey. Output written to {gr_output_path}."
    )
    create_section_separator()

    # Combine result
    json_file_list = jc.get_json_file_list(gr_output_path)
    if len(json_file_list) == 0:
        sys.exit("No json file found. Something went wrong.")
    combined_corpus_dict = jc.combine_all_json(json_file_list)
    combined_filename = jc.save_output_json(combined_corpus_dict, gr_output_path)
    final_json_path = output_path / f"{name}.json"

    # Copy result to the main dir and rename
    shutil.copyfile(combined_filename, final_json_path)

    click.echo(f"Corpus json combined into {final_json_path}")
    create_section_separator()

    # Clean up tmp dir
    shutil.rmtree(tmp_dir_path)
    click.echo("Tmp data cleaned up. Enjoy!")


@cli.command()
def view():
    click.echo("You're viewing something")
