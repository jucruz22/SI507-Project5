import unittest
from SI507project5_code import * # import everything from that script...

class Project5Tests(unittest.TestCase):
    def setUp(self):
        self.blogfile = open("tumblr_blogs_followed.csv")
        self.tagfile = open("social_justice_blogs.csv")
        self.sample_blog_inst = TumblrBlog(tumblr_blogs[0])
        self.sample_tag_inst = TumblrTag(tumblr_tags[0])

    def test_files_exist(self):
        self.assertTrue(self.blogfile.read())
        self.assertTrue(self.tagfile.read())

    def test_tumblrblog_constructor(self):
        self.assertIsInstance(self.sample_blog_inst.name, str)
        self.assertTrue(self.sample_blog_inst.title, str)
        self.assertIsInstance(self.sample_blog_inst.description, str)
        self.assertIsInstance(self.sample_blog_inst.url, str)

    def test_tumblrtag_constructor(self):
        self.assertIsInstance(self.sample_tag_inst.type, str)
        self.assertTrue(self.sample_tag_inst.blog_name, str)
        self.assertIsInstance(self.sample_tag_inst.url, str)
        self.assertIsInstance(self.sample_tag_inst.id, int)
        self.assertIsInstance(self.sample_tag_inst.related_tags, list)

    def test_list_vars(self):
        self.assertIsInstance(blog_objects,list)
        self.assertIsInstance(tag_objects, list)

    def test_list_elem_types(self):
        self.assertIsInstance(blog_objects[0],TumblrBlog)
        self.assertIsInstance(blog_objects[-1],TumblrBlog)
        self.assertIsInstance(tag_objects[0],TumblrTag)
        self.assertIsInstance(tag_objects[-1],TumblrTag)

    def tearDown(self):
        self.blogfile.close()
        self.tagfile.close()



if __name__ == "__main__":
    unittest.main(verbosity=2)
