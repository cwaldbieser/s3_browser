
S3 Browser
==========

A simple application for browsing and performing basic file operations on
objects in an S3 bucket.  Operations supported are:

* list files
* create folder
* remove folder
* download file
* upload file
* remove file

These permissions can be configured on a per-user basis.


Web Privacy & Security
----------------------

Firefox
"""""""

Firefox 101.0.1 would not successfully run the download script without some
tweaking.

tl;dr
Add the setting `privacy.restrict3rdpartystorage.skip_list` in `about:config` if it's not there already.  Add an entry that allows your first-party domain to allow a third party domain to use storage.  E.g.

    privacy.restrict3rdpartystorage.skip_list:  https://mwps8d59de.execute-api.us-east-1.amazonaws.com,https://jimmywarting.github.io

This might be mitigated by self-hosting the mitm.html frame.  This requires
further research.  The symptoms included messages in the console:

* ERROR:   Failed to get service worker registration(s): Storage access is
  restricted in this context due to user settings or private browsing mode.
* ERROR:   Uncaught (in promise) DOMException: The operation is insecure.
* WARNING: Partitioned cookie or storage access was provided to
  “https://jimmywarting.github.io/StreamSaver.js/mitm.html?version=2.0.0”
  because it is loaded in the third-party context and dynamic state
  partitioning is enabled.

It is the last warning that has a link to what is going wrong.  The
documentation about this is here:
https://developer.mozilla.org/en-US/docs/Web/Privacy/State_Partitioning#disable_dynamic_state_partitioning
