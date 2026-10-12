"""Tests for CodeBlock rendering, registration and reading-time handling."""

from wagtail_feathers.blocks import CodeBlock, CommonContentBlock
from wagtail_feathers.mixins import ReadingTimeMixin
from wagtail_feathers.models.base import FeatherBasePage

SAMPLE_CODE = 'def hello(name):\n    return "<b>" + name + " & co</b>"\n'


def make_value(block, **overrides):
    """Build a CodeBlock StructValue from raw data."""
    data = {"language": "python", "code": SAMPLE_CODE, "caption": ""}
    data.update(overrides)
    return block.to_python(data)


class TestCodeBlockRendering:
    """CodeBlock renders escaped code inside a figure/pre/code structure."""

    def test_renders_language_class(self):
        """The code element carries a language-* class for highlighters to hook."""
        block = CodeBlock()
        html = block.render(make_value(block))
        assert '<code class="language-python">' in html

    def test_escapes_html_in_code(self):
        """Angle brackets and ampersands in code are HTML-escaped."""
        block = CodeBlock()
        html = block.render(make_value(block))
        assert "&lt;b&gt;" in html
        assert "&amp; co" in html
        assert "<b>" not in html

    def test_preserves_whitespace_exactly(self):
        """Newlines and indentation inside the pre element are untouched."""
        block = CodeBlock()
        html = block.render(make_value(block))
        expected = "<pre><code class=\"language-python\">def hello(name):\n    return &quot;&lt;b&gt;&quot; + name + &quot; &amp; co&lt;/b&gt;&quot;\n</code></pre>"
        assert expected in html

    def test_figure_wrapper(self):
        """The block is wrapped in a figure element."""
        block = CodeBlock()
        html = block.render(make_value(block))
        assert html.lstrip().startswith("<figure")
        assert "</figure>" in html

    def test_caption_rendered_when_set(self):
        """A figcaption appears only when a caption is provided."""
        block = CodeBlock()
        html = block.render(make_value(block, caption="hello.py"))
        assert "<figcaption" in html
        assert "hello.py" in html

    def test_no_caption_when_empty(self):
        """No figcaption element is rendered for an empty caption."""
        block = CodeBlock()
        html = block.render(make_value(block))
        assert "<figcaption" not in html


class TestCodeBlockRegistration:
    """CodeBlock is registered in CommonContentBlock next to the Markdown block."""

    def test_code_block_registered(self):
        """CommonContentBlock exposes a code_block child of type CodeBlock."""
        stream = CommonContentBlock()
        assert isinstance(stream.child_blocks["code_block"], CodeBlock)

    def test_code_block_follows_markdown(self):
        """code_block is placed right after markdown_block."""
        names = list(CommonContentBlock().child_blocks.keys())
        assert names.index("code_block") == names.index("markdown_block") + 1

    def test_markdown_icon_differs_from_code(self):
        """Markdown and Code blocks have distinct icons in the chooser."""
        stream = CommonContentBlock()
        assert stream.child_blocks["code_block"].meta.icon == "code"
        assert stream.child_blocks["markdown_block"].meta.icon != "code"


class TestReadingTimeIgnoresCode:
    """ReadingTimeMixin does not count code as prose."""

    def test_code_not_counted_caption_counted(self):
        """Only the caption of a code block contributes to the word count."""

        class Counter:
            _count_streamfield_words = ReadingTimeMixin._count_streamfield_words
            _count_text_words = ReadingTimeMixin._count_text_words

        field = FeatherBasePage._meta.get_field("body")
        body = field.to_python(
            [
                {"type": "paragraph_block", "value": "<p>one two three four</p>"},
                {
                    "type": "code_block",
                    "value": {
                        "language": "python",
                        "code": "import os\nimport sys\nprint(os.path.join(sys.argv[0], 'many words here in code'))",
                        "caption": "two words",
                    },
                },
            ]
        )
        assert Counter()._count_streamfield_words(body) == 6
