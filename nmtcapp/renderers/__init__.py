"""Output renderers for NMTC application documents."""

__all__ = [
    "MarkdownApplicationBuilder",
    "WordApplicationBuilder",
    "ExcelApplicationBuilder",
    "PDFApplicationBuilder",
]


def __getattr__(name):
    if name == "MarkdownApplicationBuilder":
        from nmtcapp.renderers.markdown_builder import MarkdownApplicationBuilder
        return MarkdownApplicationBuilder
    if name == "WordApplicationBuilder":
        from nmtcapp.renderers.word_builder import WordApplicationBuilder
        return WordApplicationBuilder
    if name == "ExcelApplicationBuilder":
        from nmtcapp.renderers.excel_builder import ExcelApplicationBuilder
        return ExcelApplicationBuilder
    if name == "PDFApplicationBuilder":
        from nmtcapp.renderers.pdf_builder import PDFApplicationBuilder
        return PDFApplicationBuilder
    raise AttributeError(f"module 'nmtcapp.renderers' has no attribute {name!r}")
