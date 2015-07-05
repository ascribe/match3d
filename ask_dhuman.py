"""A GUI app to get information about the similarity
of images in the specified images directory, for
storage in a DHuman database (which gets stored in some
dhuman_db.* files in the images directory).
"""

import wx
import argparse
from dhuman import DHuman


class SimAsker(wx.Frame):

    def __init__(self, parent, title, d_human):
        wx.Frame.__init__(self, parent, title=title, size=(500, 930))
        self.d_human = d_human
        self.max_sz = 348  # Maximum width or height of images in GUI

        panel = wx.Panel(self, wx.ID_ANY)

        self.bitmap1 = wx.StaticBitmap(panel, bitmap=wx.EmptyBitmap(self.max_sz, self.max_sz))
        self.bitmap2 = wx.StaticBitmap(panel, bitmap=wx.EmptyBitmap(self.max_sz, self.max_sz))

        btn = wx.Button(panel, label="Next")
        btn.Bind(wx.EVT_BUTTON, self.onBtn)

        self.loadNewImages()

        l1 = "V: Very similar. Both bulk similarity and details similarity."
        l2 = "S: Similar. Either bulk similarity or details similarity but not both."
        l3 = "D: Different. Neither bulk similarity nor details similarity."

        self.radio1 = wx.RadioButton(panel, label=l1, style=wx.RB_GROUP)
        self.radio2 = wx.RadioButton(panel, label=l2)
        self.radio3 = wx.RadioButton(panel, label=l3)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.bitmap1, 0, wx.ALL, 5)
        sizer.Add(self.bitmap2, 0, wx.ALL, 5)
        sizer.Add(self.radio1, 0, wx.ALL, 5)
        sizer.Add(self.radio2, 0, wx.ALL, 5)
        sizer.Add(self.radio3, 0, wx.ALL, 5)
        sizer.Add(btn, 0, wx.ALL, 5)

        panel.SetSizer(sizer)

    def loadNewImages(self):
        self.pair_key, self.impath1, self.impath2 = self.d_human.pair_to_compare()

        print "self.pair_key = ", self.pair_key
        print "self.impath1 = ", self.impath1
        print "self.impath2 = ", self.impath2

        if self.pair_key == 'no_images_left_to_compare':
            print 'No images left to compare.'
            print 'Closing the GUI.'
            self.Close()
        else:
            img1 = wx.Image(self.impath1, wx.BITMAP_TYPE_ANY)
            new_w, new_h = rescale(img1.GetWidth(), img1.GetHeight(), self.max_sz)
            img1 = img1.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
            self.bitmap1.SetBitmap(wx.BitmapFromImage(img1))

            img2 = wx.Image(self.impath2, wx.BITMAP_TYPE_ANY)
            new_w, new_h = rescale(img2.GetWidth(), img2.GetHeight(), self.max_sz)
            img2 = img2.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
            self.bitmap2.SetBitmap(wx.BitmapFromImage(img2))

            self.Refresh()

    def onBtn(self, event):
        if self.radio1.GetValue():
            user_selection = 'V'
        elif self.radio2.GetValue():
            user_selection = 'S'
        else:
            user_selection = 'D'
        print "You selected", user_selection

        print "Storing that at key ", self.pair_key
        self.d_human.set_value_at(self.pair_key, user_selection)

        self.loadNewImages()


def rescale(W, H, smax):
    if W > H:
        NewW = smax
        NewH = smax * H / W
    else:
        NewH = smax
        NewW = smax * W / H
    return NewW, NewH


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='GUI app to ask and save info about image similarity')
    parser.add_argument('-i', '--images_dir',
                        help="""Directory containing the image files,
                         and where dhuman_db.* will get saved""",
                        required=True)
    args = parser.parse_args()

    dh = DHuman(args.images_dir)

    app = wx.App(False)
    asker = SimAsker(None, 'Similarity asker', dh).Show(True)
    app.MainLoop()

    dh.close()
