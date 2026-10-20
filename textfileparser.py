import re
from markupsafe import escape

#format [[files/file_path:link_name]]

def parse_file(text, level:int=0):
    text = str(escape(text))
    text = parse_file_links(text)
    text = parse_file_markup(text)
    text = parse_file_images(text)
    text = parse_redactions(text, level)
    return text

def parse_file_links(text): #parses a string of text and replaces chunks with the correct format with HTML links
    text = re.sub(r"\[\[(.*?)\:(.*?)\]\]", r'<a href="/files/\1">\2</a>', text)
    return text

def parse_file_markup(text):
    text = re.sub(r"==(.*?)==", r"<b>\1</b>", text) #bold text
    text = re.sub(r"\*\*(.*?)\*\*", r"<i>\1</i>", text) #italicize text
    text = re.sub(r"__(.*?)__", r"<u>\1</u>", text) #underline text
    text = re.sub(r"--(.*?)--", r"<s>\1</s>", text) #italicize text
    text = re.sub(r"{sub}(.*?){sub}", r"<sub>\1</sub>", text) #subscript
    text = re.sub(r"\^\^(.*?)\^\^", r"<sup>\1</sup>", text) #superscript
    text = re.sub(r"\|\|(.*?)\|\|", r"<mark>\1</mark>", text) #highlighted

    text = re.sub(r"{box}(.*?){box}", r'<p class="insetbox">\1</p>', text, flags=re.DOTALL) #inset box

    return text

def parse_file_images(text):
    text = re.sub(r"{{(.*?)\:(.*?)x(.*?)}}", r'<img src="/getfile/\1" style="width:\2px;height:\3px;">', text)
    #text = re.sub(r"{\[files/(.*?)\:(.*?)x(.*?)\]}", r'<video width="\x" height="\3" controls><source src="{{filepath}}" type="video/#"></video>', text)
    return text

def parse_redactions(text, current_level:int=0):
    pattern = r"{R:(.*?)}(.*?){R}"

    def redact_text(match):
        level = match.group(1)
        text = match.group(2)

        try:
            level = int(level)
        except:
            level = 0

        if current_level < level:
            return "[!:CLEARANCE]"
        else:
            return text

    text = re.sub(pattern, redact_text, text, flags=re.DOTALL)
    return text