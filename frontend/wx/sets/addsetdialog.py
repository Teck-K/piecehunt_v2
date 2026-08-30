"""Dialog window to ask the user for a set number to add"""

import wx


class AddSetDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Add Lego Set")

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.error = wx.StaticText(self, label="")
        self.error.SetForegroundColour("red")

        self.processing = wx.StaticText(self, label="")
        self.processing.SetForegroundColour("green")

        label = wx.StaticText(self, label="Set number")
        sizer.Add(label, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)
        self.input = wx.TextCtrl(self)
        sizer.Add(self.input, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)
        sizer.Add(self.error, 0, wx.ALIGN_CENTER, 5)

        btns = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(btns, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.SetSizerAndFit(sizer)

    def get_set_number(self):
        return self.input.GetValue().strip()

    def set_error(self, msg):
        self.error.SetLabel(msg)
        self.Layout()
