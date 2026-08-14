from random import randint
import tempfile


class Metadata:
    def __init__(self, title: str, metadatas: dict[str, str], freetext: str, temp_dir: tempfile.TemporaryDirectory):
        self.title: str = title
        self.metadatas: dict[str, str] = metadatas
        self.freetext: str = freetext
        self.temp_dir = temp_dir

    def get_string(self) -> str:
        # Header
        parts = [f"{' '*36}|╲   ╱|\n{' '*36}⎛ •˕• ⎞\n╭{self.line(31)}┄⎛  ≽_ ʷ _≼  ⎞┄{self.line(31)}╮\n│{' '*32}⎝╱{' '*9}╲⎠{' '*32}│\n"]

        # Title
        if self.title != "":
            parts.append(f"│{' '*(39 - len(self.title) // 2 - len(self.title) % 2)}{self.title}{' '*(38 - len(self.title) // 2)}│\n├{self.line(77)}┤\n")

        # Metadata
        parts.append(f"│{' '*34}[METADATA]{' '*33}│\n")
        for k, v in self.metadatas.items():
            parts.append(f"│ {k}: {v}{' ' * (78 - len(k) - len(v) - 4)}")
            if len(k) + len(v) + 4 < 78:
                parts.append("│\n")
            else:
                parts.append("\n")

        # Freetext
        if self.freetext != "":
            parts.append(f"├{self.line(77)}┤\n│{' '*34}[FREETEXT]{' '*33}│\n")
            paragraphs = self.freetext.split("\n")
            for paragraph in paragraphs:
                parts.append(f"│ ")
                words = paragraph.split()
                line_len = 0 # max = 75
                while len(words) != 0:
                    if line_len == 0 and len(words[0]) > 76:
                        parts.append(f"{words.pop(0)}\n│ ")
                    elif line_len + len(words[0]) + 1 < 76:
                        line_len += len(words[0]) + 1
                        parts.append(f"{words.pop(0)} ")
                    else:
                        parts.append(f"{' ' * (76 - line_len)}│\n│ ")
                        line_len = 0
                parts.append(f"{' ' * (76 - line_len)}│\n")


        # Footer
        parts.append(f"╰{self.line(77)}╯\n{' '*34}⎝╱  ╲ ╲  ╲⎠\n{' '*39}) )\n{' '*39}⎝╱\n")
        
        return "".join(parts)

    def make_file(self) -> str:
        new_file_path = f"{self.temp_dir.name}/{id(self)}.txt"
        with open(new_file_path, mode = "x", encoding = "UTF-8") as file:
            file.write(self.get_string())
        return new_file_path

    def line(self, n):
        line = []
        sep_char = "─"
        flowers = ["❀", "✿", "✾", "❁"]
        while sum(map(len, line)) < n:
            if sum(map(len, line)) < n - 7 and randint(0, 50) == 0:
                if randint(0, 1) == 0:
                    line.append(f"┄ °{flowers[randint(0, len(flowers) - 1)]}. ┄")
                else:
                    line.append(f"┄ .{flowers[randint(0, len(flowers) - 1)]}° ┄")
            else:
                line.append(sep_char)
        return "".join(line)

