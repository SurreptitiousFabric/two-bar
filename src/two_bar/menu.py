"""Parse menu JSONC and edit owned text without reformatting user settings."""
import json
import re


TOKEN = re.compile(r'(?P<string>"(?:\\.|[^"\\])*")|(?P<comment>//[^\n]*|/\*[\s\S]*?\*/)|(?P<space>\s+)|.')


def tokens(text):
    return [match for match in TOKEN.finditer(text)
            if match.lastgroup not in ("comment", "space")]


def jsonc(text):
    # Preserve offsets and token boundaries while ignoring comments/separators.
    clean = list(text)
    for match in TOKEN.finditer(text):
        if match.lastgroup == "comment":
            clean[match.start():match.end()] = re.sub(r"[^\r\n]", " ", match[0])
    significant = tokens(text)
    for index, token in enumerate(significant[:-1]):
        if (token[0] == "," and significant[index + 1][0] in ("}", "]")
                and index and significant[index - 1][0] not in ("{", "[", ",", ":")):
            clean[token.start()] = " "
    return json.loads("".join(clean))


def menu_object(text):
    """Return effective items and the tokens bounding their object."""
    parsed = jsonc(text)
    if not isinstance(parsed, dict):
        raise ValueError("Menu extension must be an object")
    significant = tokens(text)
    start = 0
    stack = []
    closing = {}
    wrapped = isinstance(parsed.get("items"), dict)
    for index, token in enumerate(significant):
        if (wrapped and len(stack) == 1 and token.lastgroup == "string"
                and json.loads(token[0]) == "items"
                and significant[index + 1][0] == ":"
                and significant[index + 2][0] == "{"):
            start = index + 2
        if token[0] in ("{", "["):
            stack.append(index)
        elif token[0] in ("}", "]"):
            closing[stack.pop()] = index
    return (parsed["items"] if wrapped else parsed), significant[start:closing[start] + 1]


def insert_menu(text, block, owned_keys):
    items, significant = menu_object(text)
    if owned_keys.intersection(items):
        raise ValueError("Existing work menu conflicts with installation")
    # An existing trailing comma already separates the new block.
    insert = ("," if significant[-2][0] not in ("{", ",") else "") + block
    offset = significant[-1].start()
    updated = text[:offset] + insert + text[offset:]
    menu_object(updated)
    return updated, insert


def remove_menu(text, block):
    if not block:
        menu_object(text)
        return text
    if text.count(block) != 1:
        raise ValueError("Work menu was edited; merge its removal manually before continuing")
    menu_object(text)
    offset = text.index(block)
    before, after = text[:offset], text[offset + len(block):]
    left, right = tokens(before), tokens(after)
    # Removing the first member, or a block using an existing trailing comma,
    # can leave an extra separator before a subsequently added member.
    if left[-1][0] in ("{", ",") and right[0][0] == ",":
        comma = right[0].start()
        after = after[:comma] + after[comma + 1:]
    updated = before + after
    menu_object(updated)
    return updated
