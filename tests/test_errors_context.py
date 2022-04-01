import pytest

from KSPUtils.errors_context import ErrorsContext, ErrorsContextError


class ErrorsContextTest(ErrorsContext):
    def _on_error(self, message: str) -> None:
        pass


def test_errors_context():
    ctx = ErrorsContextTest()
    with ctx("block1"):
        ctx.error("Error")
    assert ctx.failed is True
    assert ctx.exit_code == int(ctx) == 1
    assert ctx.blocks == ["block1"]
    assert ctx._errors == {"block1": ["[block1] Error"]}


def test_errors_context_error_outside_block():
    ctx = ErrorsContextTest()
    with pytest.raises(ErrorsContextError):
        ctx.error("error")
    ctx("block")
    with pytest.raises(ErrorsContextError):
        ctx.error("error")
    with ctx("block"):
        ctx("block1")
        with pytest.raises(ErrorsContextError):
            ctx.error("error")
    assert ctx.failed is False
    assert ctx.exit_code == int(ctx) == 0
    assert ctx._errors == {}


def test_errors_context_handle_exceptions():
    ctx = ErrorsContextTest(ValueError, RuntimeError)
    with ctx("block1"):
        raise ValueError("Error")
    assert ctx.failed is True
    assert ctx.exit_code == int(ctx) == 1
    assert ctx.blocks == ["block1"]
    assert ctx._errors == {"block1": ["[block1] Error"]}
    with ctx("block2"):
        raise RuntimeError("Error")
    assert ctx.blocks == ["block1", "block2"]
    assert ctx._errors == {"block1": ["[block1] Error"], "block2": ["[block2] Error"]}


def test_errors_context_handle_exceptions_block():
    ctx = ErrorsContextTest(ValueError)
    with ctx("block1"):
        raise ValueError("Error")
    with ctx("block2", RuntimeError):
        raise ValueError("Error1")
    with ctx("block2", RuntimeError):
        raise RuntimeError("Error2")
    assert ctx.blocks == ["block1", "block2"]
    assert ctx._errors == {
        "block1": ["[block1] Error"],
        "block2": ["[block2] Error1", "[block2] Error2"],
    }


def test_errors_context_custom_message_template():
    ctx = ErrorsContextTest()
    ctx.message_template = "{message} from {block.name}"
    with ctx("block1"):
        ctx.error("Error")
    assert ctx._errors == {"block1": ["Error from block1"]}


def test_errors_context_nested():
    ctx = ErrorsContextTest()
    with ctx("block1"):
        ctx.error("Error1.1")
        with ctx("block2"):
            ctx.error("Error2.1")
            ctx.error("Error2.2")
        ctx.error("Error1.2")
    assert ctx.blocks == ["block1", "block2"]
    assert ctx._errors == {
        "block1": ["[block1] Error1.1", "[block1] Error1.2"],
        "block2": ["[block2] Error2.1", "[block2] Error2.2"],
    }
