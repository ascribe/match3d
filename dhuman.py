"""Defines a class DHuman for getting, storing, and retrieving
information about how humans perceive the similarity of pairs
of images. DHuman(im1, im2) can be thought of as a symmetric matrix
of tokens, where initially we know nothing (except the diagonal)
so most of the entries are unknown ('?' tokens).
'V' = very similar
'S' = similar
'D' = different
'?' = unknown similarity (not actually stored)
DHuman is stored internally as a dictionary with keys of the form
'catphoto7.png,chucks-dog.jpg'.
This implementation is for relatively small sets of images.
If you want one for big sets:
- Change the persistent dictionary store to a large-scale
  key-value store.
- Stop keeping track of all the unwritten keys (image pairs).
  Just pick them randomly and skip any that are already written.
"""

import shelve

from os import listdir
from os.path import join, basename, splitext
from random import randrange
from PIL import Image


class DHuman:

    def __init__(self, images_path):
        self.images_path = images_path
        self.shelf_path = join(images_path, 'dhuman_db')
        # Open the shelf / database / persistent dictionary
        self.internal_dict = shelve.open(self.shelf_path)
        # Make a list of all image files in images_path
        name_list = []
        for fn in listdir(images_path):
            bname = basename(fn)
            _, ext = splitext(bname)
            if ext.lower() in ['.png', '.gif', '.jpg', '.jpeg']:
                name_list.append(bname)
        #print 'name_list: {}'.format(name_list)
        # Make a list of unwritten keys
        self.unwritten_keys = []
        for name1 in name_list:
            for name2 in name_list:
                if (name1 < name2):
                    key = name1 + ',' + name2
                    if not self.internal_dict.has_key(key):
                        self.unwritten_keys.append(key)
        #print 'self.unwritten_keys: {}'.format(self.unwritten_keys)
        print '{} pairs left to compare.'.format(len(self.unwritten_keys))

    def close(self):
        "Close the database."
        self.internal_dict.close()

    def pair_to_compare(self):
        """Find two images that haven't been compared yet and return:
        key, image1_path, image2_path. Used by external GUIs.
        """
        if len(self.unwritten_keys) == 0:
            return 'no_images_left_to_compare', None, None
        else:
            random_index = randrange(0, len(self.unwritten_keys))
            key = self.unwritten_keys[random_index]
            key_list = key.split(',')
            img_path1 = join(self.images_path, key_list[0])
            img_path2 = join(self.images_path, key_list[1])
            return key, img_path1, img_path2

    def compare_then_save(self):
        """Ask a human to compare two images which haven't been compared
        yet, then save their response.
        """
        if len(self.unwritten_keys) == 0:
            print "There are no more pairs of images to compare."
        else:
            random_index = randrange(0, len(self.unwritten_keys))
            key = self.unwritten_keys[random_index]
            key_list = key.split(',')
            img_path1 = join(self.images_path, key_list[0])
            img_path2 = join(self.images_path, key_list[1])
            img1 = Image.open(img_path1)
            img2 = Image.open(img_path2)
            tn_size = 400  # thumbnail size
            img1.thumbnail((tn_size, tn_size), Image.ANTIALIAS)
            img2.thumbnail((tn_size, tn_size), Image.ANTIALIAS)
            img = Image.new('RGB', (2 * tn_size, tn_size))
            img.paste(img1, (0, 0))
            img.paste(img2, (tn_size, 0))
            img.show()
            print "Showing {} and {}".format(key_list[0], key_list[1])
            # Ask for human input
            human_answer = ''
            accepted_responses = ['V', 'S', 'D', 'v', 's', 'd']
            while not (human_answer in accepted_responses):
                human_answer = raw_input("Are those very similar (V), similar (S), or different (D)? ")
                if not (human_answer in accepted_responses):
                    print "You entered {}".format(human_answer)
                    print "but accepted responses are {}".format(accepted_responses)

            value_to_save = human_answer.upper()
            self.internal_dict[key] = value_to_save
            del self.unwritten_keys[random_index]

            print "Saved the value '{}' at the key '{}'".format(value_to_save, key)

    def set_value_at_key(self, key, value):
        """Set the value of DHuman at the given key. Used by external GUIs.
        Be careful! Note that it doesn't check if the key is valid. The
        assumption is that the external GUI got the key from pair_to_compare().
        """
        self.internal_dict[key] = value
        key_index = self.unwritten_keys.index(key)
        del self.unwritten_keys[key_index]

    def get_value_at(self, im1_name, im2_name):
        """Return dhuman(im1_name, im2_name) = the similarity of the images
        with filenames im1_name and im2_name, if known. Return '?' if not
        known."""
        # Ensure we have the base names of the image files (not whole paths)
        name1 = basename(im1_name)
        name2 = basename(im2_name)

        # In Python 2.7, "Strings are compared lexicographically using the
        # numeric equivalents (the result of the built-in function ord())
        # of their characters."
        if name1 == name2:
            return 'V'
        else:
            if name1 < name2:
                key = name1 + ',' + name2
            else:
                # name1 > name2
                key = name2 + ',' + name1
            if self.internal_dict.has_key(key):
                return self.internal_dict[key]
            else:
                return '?'
