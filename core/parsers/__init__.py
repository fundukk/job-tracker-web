"""
Job parser modules.

Each parser exposes a parse() function that returns a standardized job_data dict.
"""

# Parser registry for easy extension
PARSERS = {
    'linkedin': 'core.parsers.linkedin',
    'handshake': 'core.parsers.handshake',
    'generic': 'core.parsers.generic',
}

__all__ = ['linkedin', 'handshake', 'generic']
