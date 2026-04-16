# Copyright (C) 2007 Giampaolo Rodola' <g.rodola@gmail.com>.
# Use of this source code is governed by MIT license that can be
# found in the LICENSE file.

"""An "authorizer" is a class handling authentications and permissions
of the FTP server. It is used by pyftpdlib.handlers.FTPHandler
class for:

- verifying user password
- getting user home directory
- checking user permissions when a filesystem read/write event occurs
- changing user when accessing the filesystem

DummyAuthorizer is the main class which handles virtual users.

UnixAuthorizer and WindowsAuthorizer are platform specific and
interact with UNIX and Windows password database.
"""

import os

from .exceptions import AuthenticationFailed

__all__ = ["DummyAuthorizer"]

# ===================================================================
# --- base class
# ===================================================================


class DummyAuthorizer:
    """Basic "dummy" authorizer class, suitable for subclassing to
    create your own custom authorizers.

    An "authorizer" is a class handling authentications and permissions
    of the FTP server.  It is used inside FTPHandler class for verifying
    user's password, getting users home directory, checking user
    permissions when a file read/write event occurs and changing user
    before accessing the filesystem.

    DummyAuthorizer is the base authorizer, providing a platform
    independent interface for managing "virtual" FTP users. System
    dependent authorizers can by written by subclassing this base
    class and overriding appropriate methods as necessary.
    """

    read_perms = "elr"
    write_perms = "adfmwMT"

    def __init__(self):
        self.user_table = {}

    def add_user(
        self,
        username,
        password,
        homedir,
        perm="elr",
        msg_login="Login successful.",
        msg_quit="Goodbye.",
    ):
        """Add a user to the virtual users table.

        AuthorizerError exceptions raised on error conditions such as
        invalid permissions, missing home directory or duplicate usernames.

        Optional perm argument is a string referencing the user's
        permissions explained below:

        Read permissions:
         - "e" = change directory (CWD command)
         - "l" = list files (LIST, NLST, STAT, MLSD, MLST, SIZE, MDTM commands)
         - "r" = retrieve file from the server (RETR command)

        Write permissions:
         - "a" = append data to an existing file (APPE command)
         - "d" = delete file or directory (DELE, RMD commands)
         - "f" = rename file or directory (RNFR, RNTO commands)
         - "m" = create directory (MKD command)
         - "w" = store a file to the server (STOR, STOU commands)
         - "M" = change file mode (SITE CHMOD command)
         - "T" = update file last modified time (MFMT command)

        Optional msg_login and msg_quit arguments can be specified to
        provide customized response strings when user log-in and quit.
        """
        if self.has_user(username):
            raise ValueError(f"user {username!r} already exists")
        if not os.path.isdir(homedir):
            raise ValueError(f"no such directory: {homedir!r}")
        homedir = os.path.realpath(homedir)
        self._check_permissions(username, perm)
        dic = {
            "pwd": str(password),
            "home": homedir,
            "perm": perm,
            "operms": {},
            "msg_login": str(msg_login),
            "msg_quit": str(msg_quit),
        }
        self.user_table[username] = dic

    def add_anonymous(self, homedir, **kwargs):
        """Add an anonymous user to the virtual users table.

        AuthorizerError exception raised on error conditions such as
        invalid permissions, missing home directory, or duplicate
        anonymous users.

        The keyword arguments in kwargs are the same expected by
        add_user method: "perm", "msg_login" and "msg_quit".

        The optional "perm" keyword argument is a string defaulting to
        "elr" referencing "read-only" anonymous user's permissions.

        Using write permission values ("adfmwM") results in a
        RuntimeWarning.
        """
        DummyAuthorizer.add_user(self, "anonymous", "", homedir, **kwargs)

    def remove_user(self, username):
        """Remove a user from the virtual users table."""
        del self.user_table[username]

    def override_perm(self, username, directory, perm, recursive=False):
        """Override permissions for a given directory."""
        self._check_permissions(username, perm)
        if not os.path.isdir(directory):
            raise ValueError(f"no such directory: {directory!r}")
        directory = os.path.normcase(os.path.realpath(directory))
        home = os.path.normcase(self.get_home_dir(username))
        if directory == home:
            raise ValueError("can't override home directory permissions")
        if not self._issubpath(directory, home):
            raise ValueError("path escapes user home directory")
        self.user_table[username]["operms"][directory] = perm, recursive

    def validate_authentication(self, username, password, handler):
        """Raises AuthenticationFailed if supplied username and
        password don't match the stored credentials, else return
        None.
        """
        msg = "Authentication failed."
        if not self.has_user(username):
            if username == "anonymous":
                msg = "Anonymous access not allowed."
            raise AuthenticationFailed(msg)
        if username != "anonymous":
            if self.user_table[username]["pwd"] != password:
                raise AuthenticationFailed(msg)

    def get_home_dir(self, username):
        """Return the user's home directory.
        Since this is called during authentication (PASS),
        AuthenticationFailed can be freely raised by subclasses in case
        the provided username no longer exists.
        """
        return self.user_table[username]["home"]

    def impersonate_user(self, username, password):
        """Impersonate another user (noop).

        It is always called before accessing the filesystem.
        By default it does nothing.  The subclass overriding this
        method is expected to provide a mechanism to change the
        current user.
        """

    def terminate_impersonation(self, username):
        """Terminate impersonation (noop).

        It is always called after having accessed the filesystem.
        By default it does nothing.  The subclass overriding this
        method is expected to provide a mechanism to switch back
        to the original user.
        """

    def has_user(self, username):
        """Whether the username exists in the virtual users table."""
        return username in self.user_table

    def has_perm(self, username, perm, path=None):
        """Whether the user has permission over path (an absolute
        pathname of a file or a directory).

        Expected perm argument is one of the following letters:
        "elradfmwMT".
        """
        if path is None:
            return perm in self.user_table[username]["perm"]

        path = os.path.normcase(path)
        for dir in self.user_table[username]["operms"]:
            operm, recursive = self.user_table[username]["operms"][dir]
            if self._issubpath(path, dir):
                if recursive:
                    return perm in operm
                if path == dir or (
                    os.path.dirname(path) == dir and not os.path.isdir(path)
                ):
                    return perm in operm

        return perm in self.user_table[username]["perm"]

    def get_perms(self, username):
        """Return current user permissions."""
        return self.user_table[username]["perm"]

    def get_msg_login(self, username):
        """Return the user's login message."""
        return self.user_table[username]["msg_login"]

    def get_msg_quit(self, username):
        """Return the user's quitting message."""
        try:
            return self.user_table[username]["msg_quit"]
        except KeyError:
            return "Goodbye."

    def _check_permissions(self, username, perm):
        for p in perm:
            if p not in self.read_perms + self.write_perms:
                raise ValueError(f"no such permission {p!r}")

    def _issubpath(self, a, b):
        """Return True if a is a sub-path of b or if the paths are equal."""
        p1 = a.rstrip(os.sep).split(os.sep)
        p2 = b.rstrip(os.sep).split(os.sep)
        return p1[: len(p2)] == p2


def replace_anonymous(callable):
    """A decorator to replace anonymous user string passed to authorizer
    methods as first argument with the actual user used to handle
    anonymous sessions.
    """

    def wrapper(self, username, *args, **kwargs):
        if username == "anonymous":
            username = self.anonymous_user or username
        return callable(self, username, *args, **kwargs)

    return wrapper
