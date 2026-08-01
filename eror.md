    cursor.execute(statement, parameters)
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: accounts.router_connection_id
[SQL: SELECT count(*) AS count_1 
FROM (SELECT accounts.id AS accounts_id, accounts.email AS accounts_email, accounts.password AS accounts_password, accounts.account_type AS accounts_account_type, accounts.status AS accounts_status, accounts.refresh_token AS accounts_refresh_token, accounts.error_message AS accounts_error_message, accounts.created_at AS accounts_created_at, accounts.updated_at AS accounts_updated_at, accounts.processed_at AS accounts_processed_at, accounts.injected_to_9router AS accounts_injected_to_9router, accounts.injected_at AS accounts_injected_at, accounts.router_connection_id AS accounts_router_connection_id 
FROM accounts) AS anon_1]
(Background on this error at: https://sqlalche.me/e/20/e3q8)
INFO:     Shutting down
INFO:     Waiting for connections to close. (CTRL+C to force quit)
INFO:     Finished server process [17620]
ERROR:    Traceback (most recent call last):
  File "C:\laragon\www\KiroApiKey\venv\lib\site-packages\uvicorn\_compat.py", line 60, in asyncio_run
    return loop.run_until_complete(main)
  File "C:\laragon\bin\python\python-3.10\lib\asyncio\base_events.py", line 633, in run_until_complete
    self.run_forever()
  File "C:\laragon\bin\python\python-3.10\lib\asyncio\windows_events.py", line 321, in run_forever
    super().run_forever()
  File "C:\laragon\bin\python\python-3.10\lib\asyncio\base_events.py", line 600, in run_forever
    self._run_once()
  File "C:\laragon\bin\python\python-3.10\lib\asyncio\base_events.py", line 1896, in _run_once
    handle._run()
  File "C:\laragon\bin\python\python-3.10\lib\asyncio\events.py", line 80, in _run
    self._context.run(self._callback, *self._args)
  File "C:\laragon\www\KiroApiKey\venv\lib\site-packages\uvicorn\server.py", line 80, in serve
    with self.capture_signals():
  File "C:\laragon\bin\python\python-3.10\lib\contextlib.py", line 142, in __exit__
    next(self.gen)
  File "C:\laragon\www\KiroApiKey\venv\lib\site-packages\uvicorn\server.py", line 340, in capture_signals
    signal.raise_signal(captured_signal)
KeyboardInterrupt

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\laragon\www\KiroApiKey\venv\lib\site-packages\starlette\routing.py", line 645, in lifespan
    await receive()
  File "C:\laragon\www\KiroApiKey\venv\lib\site-packages\uvicorn\lifespan\on.py", line 137, in receive
    return await self.receive_queue.get()
  File "C:\laragon\bin\python\python-3.10\lib\asyncio\queues.py", line 159, in get
    await getter
asyncio.exceptions.CancelledError