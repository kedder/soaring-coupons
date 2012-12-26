# -*- coding: utf-8 -*-
import os
import jinja2

def filter_error(value):
    if not value:
        return ''
    return jinja2.Markup("<span class='error'>%s</span>" % value)

def render_template(name, values={}):
    return jinja_environment.get_template(name).render(values)

def write_template(response, name, values={}):
    response.out.write(render_template(name, values))

loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__),
                                              'templates'))
jinja_environment = jinja2.Environment(autoescape=True,
                                       undefined=jinja2.StrictUndefined,
                                       loader=loader)
jinja_environment.filters['error'] = filter_error
