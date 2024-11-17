import logging

from fastapi.templating import Jinja2Templates as BaseJinja2Templates
from typing import Any, Optional
from gettext import ngettext

from app.utils.translation import gettext_lazy as _

from app.conf.config import structure_settings
from app.utils.datetime.timezone import now

try:
    import jinja2

    # @contextfunction renamed to @pass_context in Jinja 3.0, to be removed in 3.1
    if hasattr(jinja2, "pass_context"):
        pass_context = jinja2.pass_context
    else:  # pragma: nocover
        pass_context = jinja2.contextfunction
except ImportError:  # pragma: nocover
    jinja2 = None  # type: ignore


class SilentUndefined(jinja2.Undefined):
    """
    Don't break page loads because vars aren't there!
    """

    def _fail_with_undefined_error(self, *args, **kwargs):
        logging.exception('JINJA2: something was undefined!')
        return ''


class Jinja2Templates(BaseJinja2Templates):
    def _create_env(self, directory: str, *args, **kwargs) -> "jinja2.Environment":
        @pass_context
        def url_for(context: dict, name: str, **path_params: Any) -> str:
            request = context["request"]
            return request.url_for(name, **path_params)

        loader = jinja2.FileSystemLoader(directory)
        env = jinja2.Environment(
            loader=loader,
            autoescape=True,
            undefined=SilentUndefined,
            # enable_async=True,
            extensions=['jinja2.ext.i18n']

        )

        env.install_gettext_callables(gettext=_, ngettext=ngettext)  # type: ignore

        env.globals["url_for"] = url_for

        env.globals['now'] = now
        return env

    def get_html(self, template_name: str, context: Optional[dict] = None):
        if context is None:
            context = {}
        template = self.get_template(template_name)
        return template.render(context)


templates = Jinja2Templates(
    directory=structure_settings.TEMPLATES.get('DIR', 'templates')
)
