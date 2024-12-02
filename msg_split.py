import re
import click
from html.parser import HTMLParser
from typing import Generator, List, Tuple

MAX_LEN = 4296

class HTMLFragmentParser(HTMLParser):
    """
    Custom HTML parser to track open tags and provide functionality
    to rebuild them for splitting HTML fragments.
    """
    def __init__(self):
        super().__init__()
        self.open_tags: List[Tuple[str, List[Tuple[str, str]]]] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        """
        Handles the opening of a tag and stores it in the open tags list.
        """
        self.open_tags.append((tag, attrs))

    def handle_endtag(self, tag: str) -> None:
        """
        Handles the closing of a tag and removes it from the open tags list.
        """
        for i in range(len(self.open_tags) - 1, -1, -1):
            if self.open_tags[i][0] == tag:
                self.open_tags.pop(i)
                break

    def get_open_tags(self) -> List[Tuple[str, List[Tuple[str, str]]]]:
        """
        Returns a copy of the list of open tags.
        """
        return self.open_tags[:]

def rebuild_open_tags(tags: List[Tuple[str, List[Tuple[str, str]]]]) -> str:
    """
    Rebuilds the open tags into valid HTML strings.

    Args:
        tags: List of open tags with their attributes.

    Returns:
        A string containing the rebuilt open tags.
    """
    result = []
    for tag, attrs in tags:
        attrs_str = " ".join(f'{key}="{value}"' for key, value in attrs)
        result.append(f"<{tag} {attrs_str}>" if attrs_str else f"<{tag}>")
    return "".join(result)

def rebuild_close_tags(tags: List[Tuple[str, List[Tuple[str, str]]]]) -> str:
    """
    Rebuilds the closing tags in reverse order.

    Args:
        tags: List of open tags with their attributes.

    Returns:
        A string containing the rebuilt closing tags.
    """
    return "".join(f"</{tag}>" for tag, _ in reversed(tags))

def split_message(source: str, max_len: int = MAX_LEN) -> Generator[str, None, None]:
    """
    Splits the original HTML message into fragments of specified length.

    Args:
        source: The HTML content to split.
        max_len: Maximum allowed length for each fragment.

    Yields:
        HTML fragments as strings, each within the max_len limit.
    """
    current_fragment: List[str] = []
    current_length: int = 0
    parser = HTMLFragmentParser()

    for match in re.finditer(r"(</?\w+[^>]*>|[^<]+)", source):  # Matches tags or text
        part: str = match.group()
        part_len: int = len(part)

        close_tags: str = rebuild_close_tags(parser.get_open_tags())
        added_tags_length: int = len(close_tags)
        
        if current_length + part_len + added_tags_length > max_len:
            fragment: str = "".join(current_fragment) + close_tags
            yield fragment

            parser.reset()
            open_tags_rebuilt: str = rebuild_open_tags(parser.get_open_tags())
            current_fragment = [open_tags_rebuilt, part]
            current_length = len(open_tags_rebuilt) + part_len

        else:
            current_fragment.append(part)
            current_length += part_len

        parser.feed(part)

    if current_fragment:
        fragment: str = "".join(current_fragment) + close_tags
        yield fragment

def read_html_from_file(file_path: str) -> str:
    """
    Reads HTML content from a file.

    Args:
        file_path: Path to the HTML file.

    Returns:
        The content of the file as a string.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# @click.command()
# @click.option("--max-len", type=int, required=True, help="Maximum length of each fragment.")
# @click.argument("file_path", type=click.Path(exists=True))
# def main(max_len: int, file_path: str):
#     """Splits an HTML message into fragments while preserving proper tag structure."""
#     # Read HTML content
#     html_content = read_html_from_file(file_path)
    
#     # Process and print fragments
#     for i, fragment in enumerate(split_message(html_content, max_len), start=1):
#         print(f"fragment #{i}: {len(fragment)} chars\n{fragment}\n")

# if __name__ == "__main__":
#     main()

if __name__ == "__main__":
    file_path = "source.html"  # Replace with your HTML file path
    html_content = read_html_from_file(file_path)
    
    for i, fragment in enumerate(split_message(html_content, MAX_LEN)):
        print(f"-- fragment {i + 1}: {len(fragment)} chars --\n{fragment}\n")
        with open(f"results/fragment_{i + 1}.html", 'w', encoding='utf-8') as file:
            file.write(fragment)
