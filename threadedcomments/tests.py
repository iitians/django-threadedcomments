"""
##################################
### Model and Moderation Tests ###
##################################
>>> import datetime
>>> from models import FreeThreadedComment, ThreadedComment, TestModel
>>> from models import MARKDOWN, TEXTILE, REST, HTML, PLAINTEXT
>>> from django.contrib.auth.models import User
>>> from django.contrib.contenttypes.models import ContentType
>>> from moderation import moderator
>>> from django.core import mail

>>> topic = TestModel.objects.create(name = "Test")
>>> user = User.objects.create_user('user', 'floguy@gmail.com', password='password')
>>> user2 = User.objects.create_user('user2', 'floguy@gmail.com', password='password')
>>> comment1 = ThreadedComment.objects.create_for_object(
...     topic, user = user, ip_address = '127.0.0.1',
...     comment = 'This is fun!  This is very fun!',
... )
>>> comment2 = ThreadedComment.objects.create_for_object(
...     topic, user = user, ip_address = '127.0.0.1',
...     comment = 'This is stupid!  I hate it!',
... )
>>> comment3 = ThreadedComment.objects.create_for_object(
...     topic, user = user, ip_address = '127.0.0.1', parent = comment2,
...     comment = 'I agree, the first comment was wrong and you are right!',
... )
>>> comment4 = ThreadedComment.objects.create_for_object(
...     topic, user = user, ip_address = '127.0.0.1',
...     comment = 'What are we talking about?',
... )
>>> comment5 = ThreadedComment.objects.create_for_object(
...     topic, user = user, ip_address = '127.0.0.1', parent = comment3,
...     comment = "I'm a fanboy!",
... )
>>> comment6 = ThreadedComment.objects.create_for_object(
...     topic, user = user, ip_address = '127.0.0.1', parent = comment1,
...     comment = "What are you talking about?",
... )

>>> moderator.register(TestModel, enable_field='is_public', auto_close_field='date', close_after=15)

>>> comment7 = ThreadedComment.objects.create_for_object(
...     topic, user = user, ip_address = '127.0.0.1',
...     comment = "Post moderator addition.  Does it still work?",
... )

>>> topic.is_public = False
>>> topic.save()

>>> comment8 = ThreadedComment.objects.create_for_object(
...     topic, user = user, ip_address = '127.0.0.1', parent = comment7,
...     comment = "This should not appear, due to enable_field",
... )

>>> moderator.unregister(TestModel)

>>> comment9 = ThreadedComment.objects.create_for_object(
...     topic, user = user, ip_address = '127.0.0.1',
...     comment = "This should appear again, due to unregistration",
... )

>>> len(mail.outbox)
0

>>> class Manager(object):
...     enable_field = 'is_public'
...     auto_close_field = 'date'
...     close_after = 15
...     akismet = False
...     email_notification = True
>>> moderator.register(TestModel, manager=Manager)

>>> comment10 = ThreadedComment.objects.create_for_object(
...     topic, user = user, ip_address = '127.0.0.1',
...     comment = "This should not appear again, due to registration with a new manager.",
... )

>>> topic.is_public = True
>>> topic.save()

>>> comment11 = ThreadedComment.objects.create_for_object(
...     topic, user = user, ip_address = '127.0.0.1', parent = comment1,
...     comment = "This should appear again.",
... )

>>> len(mail.outbox)
1

>>> topic.date = topic.date - datetime.timedelta(days = 20)
>>> topic.save()

>>> comment12 = ThreadedComment.objects.create_for_object(
...     topic, user = user, ip_address = '127.0.0.1', parent = comment7,
...     comment = "This shouldn't appear, due to close_after=15.",
... )

>>> tree = ThreadedComment.public.get_tree(topic)
>>> for comment in tree:
...     print "%s %s" % ("    " * comment.depth, comment.comment)
 This is fun!  This is very fun!
     What are you talking about?
     This should appear again.
 This is stupid!  I hate it!
     I agree, the first comment was wrong and you are right!
         I'm a fanboy!
 What are we talking about?
 Post moderator addition.  Does it still work?
 This should appear again, due to unregistration

>>> tree = ThreadedComment.objects.get_tree(topic)
>>> for comment in tree:
...     print "%s %s" % ("    " * comment.depth, comment.comment)
 This is fun!  This is very fun!
     What are you talking about?
     This should appear again.
 This is stupid!  I hate it!
     I agree, the first comment was wrong and you are right!
         I'm a fanboy!
 What are we talking about?
 Post moderator addition.  Does it still work?
 This should appear again, due to unregistration
>>>
############################
### Views and URLs Tests ###
############################
>>> from django.core.urlresolvers import reverse
>>> from django.test.client import Client
>>> from django.utils.simplejson import loads
>>> from xml.dom.minidom import parseString

>>> topic = TestModel.objects.create(name = "Test2")
>>> old_topic = topic
>>> content_type = ContentType.objects.get_for_model(topic)
>>>
  ###########################################
  ### FreeThreadedComments URLs Testsests ###
  ###########################################
>>> c = Client()

>>> url = reverse('tc_free_comment', 
...     kwargs={'content_type': content_type.id, 'object_id' : topic.id}
... )
>>> response = c.post(url, {'comment' : 'test1', 'name' : 'eric', 'website' : 'http://www.eflorenzano.com/', 'email' : 'floguy@gmail.com', 'next' : '/'})
>>> FreeThreadedComment.objects.latest().get_base_data(show_dates=False)
{'website': u'http://www.eflorenzano.com/', 'comment': u'test1', 'name': u'eric', 'parent': None, 'markup': 'plaintext', 'content_object': <TestModel: TestModel object>, 'is_public': True, 'ip_address': None, 'email': u'floguy@gmail.com', 'is_approved': True}

>>> url = reverse('tc_free_comment_ajax', 
...     kwargs={'content_type': content_type.id, 'object_id' : topic.id,
...         'ajax' : 'json'}
... )
>>> response = c.post(url, {'comment' : 'test2', 'name' : 'eric', 'website' : 'http://www.eflorenzano.com/', 'email' : 'floguy@gmail.com'})
>>> tmp = loads(response.content)
>>> FreeThreadedComment.objects.latest().get_base_data(show_dates=False)
{'website': u'http://www.eflorenzano.com/', 'comment': u'test2', 'name': u'eric', 'parent': None, 'markup': 'plaintext', 'content_object': <TestModel: TestModel object>, 'is_public': True, 'ip_address': None, 'email': u'floguy@gmail.com', 'is_approved': True}

>>> url = reverse('tc_free_comment_ajax', 
...     kwargs={'content_type': content_type.id, 'object_id' : topic.id,
...         'ajax' : 'xml'}
... )
>>> response = c.post(url, {'comment' : 'test3', 'name' : 'eric', 'website' : 'http://www.eflorenzano.com/', 'email' : 'floguy@gmail.com', 'next' : '/'})
>>> tmp = parseString(response.content)
>>> FreeThreadedComment.objects.latest().get_base_data(show_dates=False)
{'website': u'http://www.eflorenzano.com/', 'comment': u'test3', 'name': u'eric', 'parent': None, 'markup': 'plaintext', 'content_object': <TestModel: TestModel object>, 'is_public': True, 'ip_address': None, 'email': u'floguy@gmail.com', 'is_approved': True}

>>> parent = FreeThreadedComment.objects.latest()

>>> url = reverse('tc_free_comment_parent', 
...     kwargs={'content_type': content_type.id, 'object_id' : topic.id, 
...         'parent_id' : parent.id}
... )
>>> response = c.post(url, {'comment' : 'test4', 'name' : 'eric', 'website' : 'http://www.eflorenzano.com/', 'email' : 'floguy@gmail.com', 'next' : '/'})
>>> FreeThreadedComment.objects.latest().get_base_data(show_dates=False)
{'website': u'http://www.eflorenzano.com/', 'comment': u'test4', 'name': u'eric', 'parent': <FreeThreadedComment: test3>, 'markup': 'plaintext', 'content_object': <TestModel: TestModel object>, 'is_public': True, 'ip_address': None, 'email': u'floguy@gmail.com', 'is_approved': True}

>>> url = reverse('tc_free_comment_parent_ajax', 
...     kwargs={'content_type': content_type.id, 'object_id' : topic.id, 
...         'parent_id' : parent.id, 'ajax' : 'json'}
... )
>>> response = c.post(url, {'comment' : 'test5', 'name' : 'eric', 'website' : 'http://www.eflorenzano.com/', 'email' : 'floguy@gmail.com'})
>>> tmp = loads(response.content)
>>> FreeThreadedComment.objects.latest().get_base_data(show_dates=False)
{'website': u'http://www.eflorenzano.com/', 'comment': u'test5', 'name': u'eric', 'parent': <FreeThreadedComment: test3>, 'markup': 'plaintext', 'content_object': <TestModel: TestModel object>, 'is_public': True, 'ip_address': None, 'email': u'floguy@gmail.com', 'is_approved': True}

>>> url = reverse('tc_free_comment_parent_ajax',
...     kwargs={'content_type': content_type.id, 'object_id' : topic.id, 
...         'parent_id' : parent.id, 'ajax' : 'xml'}
... )
>>> response = c.post(url, {'comment' : 'test6', 'name' : 'eric', 'website' : 'http://www.eflorenzano.com/', 'email' : 'floguy@gmail.com'})
>>> tmp = parseString(response.content)
>>> FreeThreadedComment.objects.latest().get_base_data(show_dates=False)
{'website': u'http://www.eflorenzano.com/', 'comment': u'test6', 'name': u'eric', 'parent': <FreeThreadedComment: test3>, 'markup': 'plaintext', 'content_object': <TestModel: TestModel object>, 'is_public': True, 'ip_address': None, 'email': u'floguy@gmail.com', 'is_approved': True}

  ###################################
  ### ThreadedComments URLs Tests ###
  ###################################
>>> u = User.objects.create_user('testuser', 'testuser@gmail.com', password='password')
>>> u.is_active = True
>>> u.save()
>>> c.login(username='testuser', password='password')
True

>>> url = reverse('tc_comment', 
...     kwargs={'content_type': content_type.id, 'object_id' : topic.id}
... )
>>> response = c.post(url, {'comment' : 'test7', 'next' : '/'})
>>> ThreadedComment.objects.latest().get_base_data(show_dates=False)
{'comment': u'test7', 'is_approved': True, 'parent': None, 'markup': 'plaintext', 'content_object': <TestModel: TestModel object>, 'user': <User: testuser>, 'is_public': True, 'ip_address': None}

>>> url = reverse('tc_comment_ajax', 
...     kwargs={'content_type': content_type.id, 'object_id' : topic.id,
...         'ajax' : 'json'}
... )
>>> response = c.post(url, {'comment' : 'test8'})
>>> tmp = loads(response.content)
>>> ThreadedComment.objects.latest().get_base_data(show_dates=False)
{'comment': u'test8', 'is_approved': True, 'parent': None, 'markup': 'plaintext', 'content_object': <TestModel: TestModel object>, 'user': <User: testuser>, 'is_public': True, 'ip_address': None}

>>> url = reverse('tc_comment_ajax', 
...     kwargs={'content_type': content_type.id, 'object_id' : topic.id,
...         'ajax' : 'xml'}
... )
>>> response = c.post(url, {'comment' : 'test9'})
>>> tmp = parseString(response.content)
>>> ThreadedComment.objects.latest().get_base_data(show_dates=False)
{'comment': u'test9', 'is_approved': True, 'parent': None, 'markup': 'plaintext', 'content_object': <TestModel: TestModel object>, 'user': <User: testuser>, 'is_public': True, 'ip_address': None}

>>> parent = ThreadedComment.objects.latest()

>>> url = reverse('tc_comment_parent', 
...     kwargs={'content_type': content_type.id, 'object_id' : topic.id, 
...         'parent_id' : parent.id}
... )
>>> response = c.post(url, {'comment' : 'test10', 'next' : '/'})
>>> ThreadedComment.objects.latest().get_base_data(show_dates=False)
{'comment': u'test10', 'is_approved': True, 'parent': <ThreadedComment: test9>, 'markup': 'plaintext', 'content_object': <TestModel: TestModel object>, 'user': <User: testuser>, 'is_public': True, 'ip_address': None}

>>> url = reverse('tc_comment_parent_ajax', 
...     kwargs={'content_type': content_type.id, 'object_id' : topic.id, 
...         'parent_id' : parent.id, 'ajax' : 'json'}
... )
>>> response = c.post(url, {'comment' : 'test11'})
>>> tmp = loads(response.content)
>>> ThreadedComment.objects.latest().get_base_data(show_dates=False)
{'comment': u'test11', 'is_approved': True, 'parent': <ThreadedComment: test9>, 'markup': 'plaintext', 'content_object': <TestModel: TestModel object>, 'user': <User: testuser>, 'is_public': True, 'ip_address': None}

>>> url = reverse('tc_comment_parent_ajax', 
...     kwargs={'content_type': content_type.id, 'object_id' : topic.id, 
...         'parent_id' : parent.id, 'ajax' : 'xml'}
... )
>>> response = c.post(url, {'comment' : 'test12'})
>>> tmp = parseString(response.content)
>>> ThreadedComment.objects.latest().get_base_data(show_dates=False)
{'comment': u'test12', 'is_approved': True, 'parent': <ThreadedComment: test9>, 'markup': 'plaintext', 'content_object': <TestModel: TestModel object>, 'user': <User: testuser>, 'is_public': True, 'ip_address': None}
>>>
#########################
### Templatetag Tests ###
#########################
>>> from django.template import Context, Template
>>> from threadedcomments.templatetags import threadedcommentstags as tags

>>> topic = TestModel.objects.create(name = "Test3")
>>> c = Context({'topic' : topic, 'parent' : comment9})

>>> Template('{% load threadedcommentstags %}{% get_comment_url topic %}').render(c)
u'/comment/9/3/'
>>> Template('{% load threadedcommentstags %}{% get_comment_url topic parent %}').render(c)
u'/comment/9/3/8/'
>>> Template('{% load threadedcommentstags %}{% get_comment_url_json topic %}').render(c)
u'/comment/9/3/json/'
>>> Template('{% load threadedcommentstags %}{% get_comment_url_xml topic %}').render(c)
u'/comment/9/3/xml/'
>>> Template('{% load threadedcommentstags %}{% get_comment_url_json topic parent %}').render(c)
u'/comment/9/3/8/json/'
>>> Template('{% load threadedcommentstags %}{% get_comment_url_xml topic parent %}').render(c)
u'/comment/9/3/8/xml/'

>>> c = Context({'topic' : topic, 'parent' : FreeThreadedComment.objects.latest()})
>>> Template('{% load threadedcommentstags %}{% get_free_comment_url topic %}').render(c)
u'/freecomment/9/3/'
>>> Template('{% load threadedcommentstags %}{% get_free_comment_url topic parent %}').render(c)
u'/freecomment/9/3/6/'
>>> Template('{% load threadedcommentstags %}{% get_free_comment_url_json topic %}').render(c)
u'/freecomment/9/3/json/'
>>> Template('{% load threadedcommentstags %}{% get_free_comment_url_xml topic %}').render(c)
u'/freecomment/9/3/xml/'
>>> Template('{% load threadedcommentstags %}{% get_free_comment_url_json topic parent %}').render(c)
u'/freecomment/9/3/6/json/'
>>> Template('{% load threadedcommentstags %}{% get_free_comment_url_xml topic parent %}').render(c)
u'/freecomment/9/3/6/xml/'

>>> c = Context({'topic' : old_topic, 'parent' : FreeThreadedComment.objects.latest()})
>>> Template('{% load threadedcommentstags %}{% get_free_threaded_comment_tree for topic as tree %}[{% for item in tree %}({{ item.depth }}){{ item.comment }},{% endfor %}]').render(c)
u'[(0)test1,(0)test2,(0)test3,(1)test4,(1)test6,(0)test5,]'

>>> Template('{% load threadedcommentstags %}{% get_threaded_comment_tree for topic as tree %}[{% for item in tree %}({{ item.depth }}){{ item.comment }},{% endfor %}]').render(c)
u'[(0)test7,(0)test8,(0)test9,(1)test10,(1)test12,(0)test11,]'

>>> markdown_txt = '''
... A First Level Header
... ====================
... 
... A Second Level Header
... ---------------------
... 
... Now is the time for all good men to come to
... the aid of their country. This is just a
... regular paragraph.
... 
... The quick brown fox jumped over the lazy
... dog's back.
... 
... ### Header 3
... 
... > This is a blockquote.
... > 
... > This is the second paragraph in the blockquote.
... >
... > ## This is an H2 in a blockquote
... '''

>>> comment_markdown = ThreadedComment.objects.create_for_object(
...     old_topic, user = user, ip_address = '127.0.0.1', markup = MARKDOWN,
...     comment = markdown_txt,
... )

>>> c = Context({'comment' : comment_markdown})
>>> Template("{% load threadedcommentstags %}{% auto_transform_markup comment %}").render(c)
u"\\n\\n<h1> A First Level Header</h1>\\n\\n<h2> A Second Level Header</h2>\\n<p>Now is the time for all good men to come to\\n   the aid of their country. This is just a\\n   regular paragraph.\\n</p>\\n<p>The quick brown fox jumped over the lazy\\n   dog's back.\\n</p>\\n\\n<h3> Header 3</h3>\\n<blockquote><p>This is a blockquote.\\n</p>\\n<p>This is the second paragraph in the blockquote.\\n</p>\\n\\n<h2> This is an H2 in a blockquote</h2>\\n</blockquote>\\n"

>>> textile_txt = '''
... h2{color:green}. This is a title
... 
... h3. This is a subhead
... 
... p{color:red}. This is some text of dubious character. Isn't the use of "quotes" just lazy ... writing -- and theft of 'intellectual property' besides? I think the time has come to see a block quote.
... 
... bq[fr]. This is a block quote. I'll admit it's not the most exciting block quote ever devised.
... 
... Simple list:
... 
... #{color:blue} one
... # two
... # three
... 
... Multi-level list:
... 
... # one
... ## aye
... ## bee
... ## see
... # two
... ## x
... ## y
... # three
... 
... Mixed list:
... 
... * Point one
... * Point two
... ## Step 1
... ## Step 2
... ## Step 3
... * Point three
... ** Sub point 1
... ** Sub point 2
... 
... 
... Well, that went well. How about we insert an <a href="/" title="watch out">old-fashioned ... hypertext link</a>? Will the quote marks in the tags get messed up? No!
... 
... "This is a link (optional title)":http://www.textism.com
... 
... table{border:1px solid black}.
... |_. this|_. is|_. a|_. header|
... <{background:gray}. |\2. this is|{background:red;width:200px}. a|^<>{height:200px}. row|
... |this|<>{padding:10px}. is|^. another|(bob#bob). row|
... 
... An image:
... 
... !/common/textist.gif(optional alt text)!
... 
... # Librarians rule
... # Yes they do
... # But you knew that
... 
... Some more text of dubious character. Here is a noisome string of CAPITAL letters. Here is ... something we want to _emphasize_. 
... That was a linebreak. And something to indicate *strength*. Of course I could use <em>my ... own HTML tags</em> if I <strong>felt</strong> like it.
... 
... h3. Coding
... 
... This <code>is some code, "isn't it"</code>. Watch those quote marks! Now for some preformatted text:
... 
... <pre>
... <code>
... 	$text = str_replace("<p>%::%</p>","",$text);
... 	$text = str_replace("%::%</p>","",$text);
... 	$text = str_replace("%::%","",$text);
... 
... </code>
... </pre>
... 
... This isn't code.
... 
... 
... So you see, my friends:
... 
... * The time is now
... * The time is not later
... * The time is not yesterday
... * We must act
... '''

>>> comment_textile = ThreadedComment.objects.create_for_object(
...     old_topic, user = user, ip_address = '127.0.0.1', markup = TEXTILE,
...     comment = textile_txt,
... )
>>> c = Context({'comment' : comment_textile})
>>> Template("{% load threadedcommentstags %}{% auto_transform_markup comment %}").render(c)
u'<h2 style="color:green;">This is a title</h2>\\n\\n<h3>This is a subhead</h3>\\n\\n<p style="color:red;">This is some text of dubious character. Isn&#8217;t the use of &#8220;quotes&#8221; just lazy&#8230; writing&#8212;and theft of &#8216;intellectual property&#8217; besides? I think the time has come to see a block quote.</p>\\n\\n<blockquote lang="fr">\\n<p>This is a block quote. I&#8217;ll admit it&#8217;s not the most exciting block quote ever devised.</p>\\n</blockquote>\\n\\n<p>Simple list:</p>\\n\\n<ol>\\n<li style="color:blue;">one</li>\\n<li>two</li>\\n<li>three</li>\\n</ol>\\n\\n<p>Multi-level list:</p>\\n\\n<ol>\\n<li>one\\n<ol>\\n<li>aye</li>\\n<li>bee</li>\\n<li>see</li>\\n</ol>\\n</li>\\n<li>two\\n<ol>\\n<li>x</li>\\n<li>y</li>\\n</ol>\\n</li>\\n<li>three</li>\\n</ol>\\n\\n<p>Mixed list:</p>\\n\\n<ul>\\n<li>Point one</li>\\n<li>Point two<br />\\n## Step 1<br />\\n## Step 2<br />\\n## Step 3</li>\\n<li>Point three\\n<ul>\\n<li>Sub point 1</li>\\n<li>Sub point 2</li>\\n</ul>\\n</li>\\n</ul>\\n\\n<p>Well, that went well. How about we insert an <a href="/" title="watch out">old-fashioned&#8230; hypertext link</a>? Will the quote marks in the tags get messed up? No!</p>\\n\\n<p><a href="http://www.textism.com" title="optional title">This is a link</a></p>\\n\\n<table style="border:1px solid black;">\\n<tr>\\n<th>this</th>\\n<th>is</th>\\n<th>a</th>\\n<th>header</th>\\n</tr>\\n<tr style="background:gray;" align="left">\\n<td>\\x02. this is</td>\\n<td style="background:red;width:200px;">a</td>\\n<td style="height:200px;" align="justify" valign="top">row</td>\\n</tr>\\n<tr>\\n<td>this</td>\\n<td style="padding:10px;" align="justify">is</td>\\n<td valign="top">another</td>\\n<td class="bob" id="bob">row</td>\\n</tr>\\n</table>\\n\\n<p>An image:</p>\\n\\n<p><img src="/common/textist.gif" title="optional alt text" alt="optional alt text" /></p>\\n\\n<ol>\\n<li>Librarians rule</li>\\n<li>Yes they do</li>\\n<li>But you knew that</li>\\n</ol>\\n\\n<p>Some more text of dubious character. Here is a noisome string of <span class="caps">CAPITAL</span> letters. Here is&#8230; something we want to <em>emphasize</em>. <br />\\nThat was a linebreak. And something to indicate <strong>strength</strong>. Of course I could use <em>my&#8230; own <span class="caps">HTML</span> tags</em> if I <strong>felt</strong> like it.</p>\\n\\n<h3>Coding</h3>\\n\\n<p>This <code>is some code, &#8220;isn&#8217;t it&#8221;</code>. Watch those quote marks! Now for some preformatted text:</p>\\n\\n<pre>\\n<code>\\n    $text = str_replace("<p>%::%</p>","",$text);\\n    $text = str_replace("%::%</p>","",$text);\\n    $text = str_replace("%::%","",$text);\\n\\n</code>\\n</pre>\\n\\n<p>This isn&#8217;t code.</p>\\n\\n<p>So you see, my friends:</p>\\n\\n<ul>\\n<li>The time is now</li>\\n<li>The time is not later</li>\\n<li>The time is not yesterday</li>\\n<li>We must act</li>\\n</ul>'


>>> rest_txt = '''
... FooBar Header
... =============
... reStructuredText is **nice**. It has its own webpage_.
... 
... A table:
... 
... =====  =====  ======
...    Inputs     Output
... ------------  ------
...   A      B    A or B
... =====  =====  ======
... False  False  False
... True   False  True
... False  True   True
... True   True   True
... =====  =====  ======
... 
... RST TracLinks
... -------------
... 
... See also ticket `#42`::.
... 
... .. _webpage: http://docutils.sourceforge.net/rst.html
... '''

>>> comment_rest = ThreadedComment.objects.create_for_object(
...     old_topic, user = user, ip_address = '127.0.0.1', markup = REST,
...     comment = rest_txt,
... )
>>> c = Context({'comment' : comment_rest})
>>> Template("{% load threadedcommentstags %}{% auto_transform_markup comment %}").render(c)
u'<p>reStructuredText is <strong>nice</strong>. It has its own <a class="reference" href="http://docutils.sourceforge.net/rst.html">webpage</a>.</p>\\n<p>A table:</p>\\n<table border="1" class="docutils">\\n<colgroup>\\n<col width="31%" />\\n<col width="31%" />\\n<col width="38%" />\\n</colgroup>\\n<thead valign="bottom">\\n<tr><th class="head" colspan="2">Inputs</th>\\n<th class="head">Output</th>\\n</tr>\\n<tr><th class="head">A</th>\\n<th class="head">B</th>\\n<th class="head">A or B</th>\\n</tr>\\n</thead>\\n<tbody valign="top">\\n<tr><td>False</td>\\n<td>False</td>\\n<td>False</td>\\n</tr>\\n<tr><td>True</td>\\n<td>False</td>\\n<td>True</td>\\n</tr>\\n<tr><td>False</td>\\n<td>True</td>\\n<td>True</td>\\n</tr>\\n<tr><td>True</td>\\n<td>True</td>\\n<td>True</td>\\n</tr>\\n</tbody>\\n</table>\\n<div class="section">\\n<h1><a id="rst-traclinks" name="rst-traclinks">RST TracLinks</a></h1>\\n<p>See also ticket <cite>#42</cite>::.</p>\\n</div>\\n'

>>> comment_html = ThreadedComment.objects.create_for_object(
...     old_topic, user = user, ip_address = '127.0.0.1', markup = HTML,
...     comment = '<b>This is Funny</b>',
... )
>>> c = Context({'comment' : comment_html})
>>> Template("{% load threadedcommentstags %}{% auto_transform_markup comment %}").render(c)
u'<b>This is Funny</b>'

>>> comment_plaintext = ThreadedComment.objects.create_for_object(
...     old_topic, user = user, ip_address = '127.0.0.1', markup = PLAINTEXT,
...     comment = '<b>This is Funny</b>',
... )
>>> c = Context({'comment' : comment_plaintext})
>>> Template("{% load threadedcommentstags %}{% auto_transform_markup comment %}").render(c)
u'&lt;b&gt;This is Funny&lt;/b&gt;'
"""