import os

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .formatter import format_discord_content, format_file_size, get_hash_path

_env = None
_template = None


def init_worker(template_dir: str):
    global _env, _template
    _env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
    _template = _env.get_template("thread.html")


def render_thread_chunk(args):
    """Worker function for multiprocessing pool to render a batch of threads."""
    threads_data, out_dir = args
    results = []

    for thread in threads_data:
        thread_id = thread.get("_id")
        recipient = thread.get("recipient") or {}
        user_id = str(recipient.get("id", ""))
        username = recipient.get("name", "")
        discriminator = recipient.get("discriminator", "")
        created_at = thread.get("created_at", "")
        closed_at = thread.get("closed_at", "")
        messages = thread.get("messages", [])

        # Pre-process messages for template
        for msg in messages:
            msg["formatted_content"] = format_discord_content(msg.get("content", ""))
            for att in msg.get("attachments", []):
                att["formatted_size"] = format_file_size(att.get("size", 0))

        rel_path = f"threads/{get_hash_path(thread_id)}"
        full_path = os.path.join(out_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        html_out = _template.render(thread=thread, recipient=recipient)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(html_out)

        results.append(
            (
                thread_id,
                user_id,
                username,
                discriminator,
                created_at,
                closed_at,
                len(messages),
                rel_path,
            )
        )

    return results
