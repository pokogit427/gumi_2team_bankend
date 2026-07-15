Static chat widget that posts to `/api/chat`.

Usage:
- Copy the contents of this folder into your frontend or serve statically from the backend.
- Include the HTML or embed the widget markup and assets.

Security / notes:
- The widget is minimal — add CSRF protection and origin validation for production.
- The widget posts to `/api/chat` and expects JSON `{message:string}` -> `{answer:string,references:[]}`.
