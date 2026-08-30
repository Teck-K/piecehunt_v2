import logging
from pathlib import Path

import wx
import wx.dataview as dv

from backend.handlers.part_handler import PartHandler
from backend.handlers.set_handler import SetHandler
from backend.handlers.user_handler import UserHandler
from services import api_client
from services.api_retry import call_with_refresh
from settings import APP_IMAGES_DIR

logger = logging.getLogger(__name__)


class MissingPartsReportDialog(wx.Frame):
    """Dialog showing a missing parts report for all sets of the current user.

    Displays a list of sets with checkboxes to select which sets to include
    in the export. Supports PDF and Excel export, with optional mail delivery.

    Args:
        parent: The parent frame (mainframe).
    """

    def __init__(self, parent):
        super().__init__(parent, title="Missing Parts Report", size=(820, 540), style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)
        self.SetIcon(wx.Icon(str(APP_IMAGES_DIR / "piecehunt_logo.ico")))
        self.mainframe = parent
        self.set_handler = SetHandler()
        self.part_handler = PartHandler()
        self.user_handler = UserHandler()
        self._all_sets: list[dict] = []

        self._init_ui()
        self._load_data()
        self.Centre()

    def _init_ui(self):
        """Builds the UI: toggles, DataViewListCtrl, select helpers and buttons."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # --- Toggles ---
        toggle_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.chk_spares = wx.CheckBox(panel, label="Include spare parts")
        self.chk_spares.SetValue(False)
        self.chk_spares.Bind(wx.EVT_CHECKBOX, self.on_toggle)

        self.chk_completed = wx.CheckBox(panel, label="Show completed sets")
        self.chk_completed.SetValue(False)
        self.chk_completed.Bind(wx.EVT_CHECKBOX, self.on_toggle)

        toggle_sizer.Add(self.chk_spares, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        toggle_sizer.Add(self.chk_completed, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        # --- Select all / none ---
        select_sizer = wx.BoxSizer(wx.HORIZONTAL)

        btn_select_all = wx.Button(panel, label="Select All", size=(90, -1))
        btn_select_all.Bind(wx.EVT_BUTTON, self.on_select_all)

        btn_select_none = wx.Button(panel, label="Select None", size=(90, -1))
        btn_select_none.Bind(wx.EVT_BUTTON, self.on_select_none)

        select_sizer.Add(btn_select_all, 0, wx.ALL, 3)
        select_sizer.Add(btn_select_none, 0, wx.ALL, 3)

        # --- DataViewListCtrl ---
        self.dv = dv.DataViewListCtrl(panel, style=dv.DV_ROW_LINES | dv.DV_HORIZ_RULES)

        self.dv.AppendToggleColumn("", width=30)
        self.dv.AppendTextColumn("Set nr", width=90)
        self.dv.AppendTextColumn("Name", width=260)
        self.dv.AppendTextColumn("Total", width=65, align=wx.ALIGN_RIGHT)
        self.dv.AppendTextColumn("Found", width=65, align=wx.ALIGN_RIGHT)
        self.dv.AppendTextColumn("Missing", width=70, align=wx.ALIGN_RIGHT)
        self.dv.AppendTextColumn("%", width=55, align=wx.ALIGN_RIGHT)

        # --- Status label ---
        self.lbl_status = wx.StaticText(panel, label="")

        # --- Buttons ---
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_pdf = wx.Button(panel, label="Export PDF ▾")
        self.btn_pdf.Bind(wx.EVT_BUTTON, self.on_pdf_menu)

        self.btn_excel = wx.Button(panel, label="Export Excel ▾")
        self.btn_excel.Bind(wx.EVT_BUTTON, self.on_excel_menu)

        btn_close = wx.Button(panel, wx.ID_CLOSE, "Close")
        btn_close.Bind(wx.EVT_BUTTON, self.on_close)

        btn_sizer.Add(self.btn_pdf, 0, wx.ALL, 5)
        btn_sizer.Add(self.btn_excel, 0, wx.ALL, 5)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(btn_close, 0, wx.ALL, 5)

        # --- Assemble ---
        main_sizer.Add(toggle_sizer, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(select_sizer, 0, wx.LEFT | wx.RIGHT, 5)
        main_sizer.Add(self.dv, 1, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(self.lbl_status, 0, wx.LEFT | wx.BOTTOM, 10)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND)

        panel.SetSizer(main_sizer)

    def _load_data(self):
        """Fetches set data and populates the DataViewListCtrl.

        Filters out completed sets if the toggle is off.
        Respects the include_spares toggle when retrieving quantities.
        All visible sets are checked by default.
        """
        include_spares = self.chk_spares.GetValue()
        show_completed = self.chk_completed.GetValue()

        logger.debug(
            "Loading missing parts report — include_spares=%s, show_completed=%s",
            include_spares,
            show_completed,
        )

        try:
            all_sets = self.set_handler.get_all_user_sets(
                include_spares=include_spares,
            )
        except Exception as e:
            logger.error("Failed to load sets for missing parts report: %s", e, exc_info=True)
            wx.MessageBox(
                "Could not load set data.\nPlease try again later.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        self._all_sets = all_sets
        self.dv.DeleteAllItems()

        visible = all_sets if show_completed else [s for s in all_sets if s["progress_pct"] < 100]

        for row in visible:
            missing = row["total_parts"] - row["found_parts"]
            self.dv.AppendItem(
                [
                    False,
                    row["set_num"],
                    row["set_name"],
                    str(row["total_parts"]),
                    str(row["found_parts"]),
                    str(missing),
                    f"{row['progress_pct']}%",
                ]
            )

        self._update_status(len(visible), len(self._all_sets))

    def _update_status(self, shown: int, total: int):
        """Updates the status label with set counts.

        Args:
            shown: Number of sets currently visible in the list.
            total: Total number of sets for the user.
        """
        self.lbl_status.SetLabel(f"Showing {shown} of {total} sets")

    def _get_selected_set_nums(self) -> list[str]:
        """Returns the set_num values of all checked rows.

        Returns:
            A list of set_num strings for the checked sets.
        """
        return [self.dv.GetTextValue(row, 1) for row in range(self.dv.GetItemCount()) if self.dv.GetToggleValue(row, 0)]

    def _validate_selection(self) -> bool:
        """Shows a message and returns False if no sets are selected.

        Returns:
            True if at least one set is selected, False otherwise.
        """
        if not self._get_selected_set_nums():
            wx.MessageBox(
                "Please select at least one set to include in the report.",
                "No Sets Selected",
                wx.OK | wx.ICON_INFORMATION,
            )
            return False
        return True

    def _get_report_data(self) -> list[dict] | None:
        """Fetches missing parts report data for the selected sets.

        Returns:
            List of part dicts, or None if fetching failed.
        """
        try:
            return self.part_handler.get_missing_parts_report_data(
                include_spares=self.chk_spares.GetValue(),
                set_nums=self._get_selected_set_nums(),
            )
        except Exception as e:
            logger.error("Failed to fetch report data: %s", e, exc_info=True)
            wx.MessageBox(
                "Could not load report data.\nPlease try again later.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return None

    def _send_report_mail(self, file_path: Path, data: list[dict]):
        """Uploads the generated report file to the backend, which emails it
        to the current user.

        Args:
            file_path: Path to the generated report file.
            data: The report data used to extract counts for the request.
        """

        set_count = len({s["set_num"] for part in data for s in part["sets"]})

        call_with_refresh(
            self.user_handler,
            api_client.email_missing_parts_report,
            file_path,
            len(data),
            set_count,
            self.chk_spares.GetValue(),
        )

        logger.info("Missing parts report mailed via API")

    def on_toggle(self, event):
        """Reloads data when a toggle checkbox changes.

        Args:
            event: The checkbox event.
        """
        self._load_data()

    def on_select_all(self, event):
        """Checks all rows in the list.

        Args:
            event: The button event.
        """
        for row in range(self.dv.GetItemCount()):
            self.dv.SetToggleValue(True, row, 0)

    def on_select_none(self, event):
        """Unchecks all rows in the list.

        Args:
            event: The button event.
        """
        for row in range(self.dv.GetItemCount()):
            self.dv.SetToggleValue(False, row, 0)

    def on_pdf_menu(self, event):
        """Shows a context menu with PDF export options.

        Args:
            event: The button event.
        """
        menu = wx.Menu()
        item_save = menu.Append(wx.ID_ANY, "Save to file")
        item_save_mail = menu.Append(wx.ID_ANY, "Save + Send by mail")

        self.Bind(wx.EVT_MENU, self._on_export_pdf, item_save)
        self.Bind(wx.EVT_MENU, lambda e: self._on_export_pdf(e, send_mail=True), item_save_mail)

        self.btn_pdf.PopupMenu(menu)
        menu.Destroy()

    def on_excel_menu(self, event):
        """Shows a context menu with Excel export options.

        Args:
            event: The button event.
        """
        menu = wx.Menu()
        item_save = menu.Append(wx.ID_ANY, "Save to file")
        item_save_mail = menu.Append(wx.ID_ANY, "Save + Send by mail")

        self.Bind(wx.EVT_MENU, self._on_export_excel, item_save)
        self.Bind(wx.EVT_MENU, lambda e: self._on_export_excel(e, send_mail=True), item_save_mail)

        self.btn_excel.PopupMenu(menu)
        menu.Destroy()

    def _on_export_pdf(self, event, send_mail: bool = False):
        """Generates a PDF report and optionally mails it.

        Args:
            event: The menu event.
            send_mail: Whether to send the report by email after saving.
        """
        if not self._validate_selection():
            return

        logger.debug("PDF export — send_mail=%s", send_mail)
        self.btn_pdf.Enable(False)

        try:
            from backend.reports.pdf_report import generate_missing_parts_pdf

            data = self._get_report_data()
            if data is None:
                return

            path = generate_missing_parts_pdf(
                data,
                username=self.user_handler.auth_session.email,
                include_spares=self.chk_spares.GetValue(),
            )

            wx.LaunchDefaultApplication(str(path))

            if send_mail:
                self._send_report_mail(path, data)
                wx.MessageBox(
                    f"Report saved and sent to {self.user_handler.auth_session.email}.",
                    "Mail Sent",
                    wx.OK | wx.ICON_INFORMATION,
                )

            logger.info("PDF export complete: %s", path.name)

        except Exception as e:
            logger.error("PDF export failed: %s", e, exc_info=True)
            wx.MessageBox(
                "Could not generate PDF.\nPlease try again later.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
        finally:
            self.btn_pdf.Enable(True)

    def _on_export_excel(self, event, send_mail: bool = False):
        """Generates an Excel report and optionally mails it.

        Args:
            event: The menu event.
            send_mail: Whether to send the report by email after saving.
        """
        if not self._validate_selection():
            return

        logger.debug("Excel export — send_mail=%s", send_mail)
        self.btn_excel.Enable(False)

        try:
            from backend.reports.excel_report import generate_missing_parts_excel

            data = self._get_report_data()
            if data is None:
                return

            path = generate_missing_parts_excel(
                data,
                username=self.user_handler.auth_session.email,
                include_spares=self.chk_spares.GetValue(),
            )

            wx.LaunchDefaultApplication(str(path))

            if send_mail:
                self._send_report_mail(path, data)
                wx.MessageBox(
                    f"Report saved and sent to {self.user_handler.auth_session.email}.",
                    "Mail Sent",
                    wx.OK | wx.ICON_INFORMATION,
                )

            logger.info("Excel export complete: %s", path.name)

        except Exception as e:
            logger.error("Excel export failed: %s", e, exc_info=True)
            wx.MessageBox(
                "Could not generate Excel file.\nPlease try again later.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
        finally:
            self.btn_excel.Enable(True)

    def on_close(self, event):
        """Closes the report dialog.

        Args:
            event: The button event.
        """
        logger.debug("Missing Parts Report dialog closed")
        self.Close()
