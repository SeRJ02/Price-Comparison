# Session Restart Instructions

When your Colab session restarts, run these cells in order:

1. **Cell 1:** `pip install` — Install dependencies from requirements.txt
2. **Cell 2:** Mount Drive — `drive.mount("/content/drive")`
3. **Cell 3:** Load commission sheet — `commission_map = load_commission_sheet()`
4. **Cell 4:** Enter Telegram token — Run the `getpass` cell
5. **Cell 5:** Start bot — Run `main()` (this blocks — must be last)

> ⚠️ `run_polling()` blocks the cell. You cannot run other cells while the bot is active.
> To stop the bot, interrupt the cell (⏹ button) then re-run from Cell 3.
