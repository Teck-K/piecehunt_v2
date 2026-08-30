import wx


class IntValidator(wx.Validator):
    """A wx.Validator that restricts input to positive integers.

    Blocks non-numeric keypresses and validates the final value
    on form submission.
    """

    def __init__(self):
        super().__init__()
        self.Bind(wx.EVT_CHAR, self.on_char)

    def Clone(self):
        return IntValidator()

    def Validate(self, parent):
        """Validates that the field contains a positive integer.

        Args:
            parent: The parent window, required by the wx.Validator interface.

        Returns:
            True if the value is a positive integer, False otherwise.
        """

        text_ctrl = self.GetWindow()
        value = text_ctrl.GetValue()
        if value.isdigit() and int(value) >= 0:
            return True
        wx.MessageBox("Please enter a positive integer", "Invalid Input")
        return False

    def on_char(self, event):
        key = event.GetKeyCode()
        if chr(key).isdigit() or key in (wx.WXK_BACK, wx.WXK_DELETE):
            event.Skip()
        else:
            return
