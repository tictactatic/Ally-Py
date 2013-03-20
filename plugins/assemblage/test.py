'''
Created on Dec 21, 2012

@author: chupy
'''

import re
from json.encoder import encode_basestring
import json

postsJSON = '''
{
  "total" : "10",
  "limit" : "10",
  "offset" : "0",
  "PostList" : [ {
    "href" : "http://localhost:8080/resources/Data/Post/1"
  }, {
    "href" : "http://localhost:8080/resources/Data/Post/2"
  }, {
    "href" : "http://localhost:8080/resources/Data/Post/3"
  }, {
    "href" : "http://localhost:8080/resources/Data/Post/4"
  }, {
    "href" : "http://localhost:8080/resources/Data/Post/5"
  }, {
    "href" : "http://localhost:8080/resources/Data/Post/6"
  }, {
    "href" : "http://localhost:8080/resources/Data/Post/7"
  }, {
    "href" : "http://localhost:8080/resources/Data/Post/8"
  }, {
    "href" : "http://localhost:8080/resources/Data/Post/9"
  }, {
    "href" : "http://localhost:8080/resources/Data/Post/11"
  } ]
}
'''
postJSON = '''
{
  "Id" : "1",
  "IsModified" : "False",
  "IsPublished" : "False",
  "AuthorName" : "Janet Editor",
  "Content" : "Hello world!",
  "CreatedOn" : "3/6/13 10:46 PM",
  "Author" : {
  "href" : "http://localhost:8080/resources/Data/Collaborator/10",
    "Id" : "10"
  },
  "Creator" : {
    "href" : "http://localhost:8080/resources/HR/User/2",
    "Id" : "2"
  },
  "Type" : {
    "href" : "http://localhost:8080/resources/Data/PostType/normal",
    "Key" : "normal"
  }
}
'''
authorJSON = '''
{
  "Id" : "10",
  "Name" : "Janet Editor",
  "Source" : {
    "href" : "http://localhost:8080/resources/Data/Source/1",
    "Id" : "1"
  },
  "User" : {
    "href" : "http://localhost:8080/resources/HR/User/2",
    "Id" : "2"
  },
  "PostList" : {
    "href" : "http://localhost:8080/resources/Data/Collaborator/10/Post/"
  },
  "PostPublishedList" : {
    "href" : "http://localhost:8080/resources/Data/Collaborator/10/Post/Published"
  },
  "PostUnpublishedList" : {
    "href" : "http://localhost:8080/resources/Data/Collaborator/10/Post/Unpublished"
  }
}
'''


postXML = '''
<Post>
    <Id>1</Id>
    <IsModified>False</IsModified>
    <IsPublished>False</IsPublished>
    <AuthorName>Janet Editor</AuthorName>
    <Content>Hello world!</Content>
    <CreatedOn>3/11/13 11:12 AM</CreatedOn>
    <Author href="http://localhost:8080/resources/Data/Collaborator/10">
        <Id>10</Id>
    </Author>
    <Creator href="http://localhost:8080/resources/HR/User/2">
        <Id>2</Id>
    </Creator>
    <Type href="http://localhost:8080/resources/Data/PostType/normal">
        <Key>normal</Key>
    </Type>
</Post>
'''
authorXML = '''
<Collaborator>
    <Id>10</Id>
    <Name>Janet Editor</Name>
    <Source href="http://localhost:8080/resources/Data/Source/1">
        <Id>1</Id>
    </Source>
    <User href="http://localhost:8080/resources/HR/User/2">
        <Id>2</Id>
    </User>
    <Post href="http://localhost:8080/resources/Data/Collaborator/10/Post/"/>
    <PostPublished href="http://localhost:8080/resources/Data/Collaborator/10/Post/Published"/>
    <PostUnpublished href="http://localhost:8080/resources/Data/Collaborator/10/Post/Unpublished"/>
</Collaborator>
'''


postYAML = '''
Author:
  Id: '10'
  href: http://localhost:8080/resources/Data/Collaborator/10.yaml
AuthorName: Janet Editor
Content: Hello world!
CreatedOn: 3/6/13 10:46 PM
Creator:
  Id: '2'
  href: http://localhost:8080/resources/HR/User/2.yaml
Id: '1'
IsModified: 'False'
IsPublished: 'False'
Type:
  Key: normal
  href: http://localhost:8080/resources/Data/PostType/normal.yaml
'''
authorYAML = '''
Id: '10'
Name: Janet Editor
PostList:
  href: http://localhost:8080/resources/Data/Collaborator/10/Post.yaml
PostPublishedList:
  href: http://localhost:8080/resources/Data/Collaborator/10/Post/Published.yaml
PostUnpublishedList:
  href: http://localhost:8080/resources/Data/Collaborator/10/Post/Unpublished.yaml
Source:
  Id: '1'
  href: http://localhost:8080/resources/Data/Source/1.yaml
User:
  Id: '2'
  href: http://localhost:8080/resources/HR/User/2.yaml
'''

if __name__ == '__main__':
 
#    matcher = re.compile('(?s){\s*("href"\s*\:\s*".*?")\s*\}')
#    reference = re.compile('"href"\s*\:\s*"([^"]*)"')
#    injector = {re.compile('^\s*\{'): '{{1},'}
#    target, response = postsJSON, postJSON

#    matcher = re.compile('("Author"\s*\:\s*\{\s*"href"\s*\:\s*"[^"\\\]*(?:\\\.[^"\\\]*)*"\,)\s*"Id"\s*\:\s*"[^"\\\]*(?:\\\.[^"\\\]*)*"\s*[\,]?\s*\}')
#    reference = re.compile('"href"\s*\:\s*"([^"\\\]*(?:\\\.[^"\\\]*)*)"\,')
#    injector = {re.compile('^\s*\{'): '{1}'}
#    target, response = postJSON, authorJSON
    
    pattern = '("%s"\s*\:\s*\{)' % 'Author'
    prop1 = '\s*("href"\s*\:\s*"[^"\\\]*(?:\\\.[^"\\\]*)*")\s*\,?'
    prop2 = '\s*"Id"\s*\:\s*"[^"\\\]*(?:\\\.[^"\\\]*)*"\s*\,?'
    pattern = '%s(?:(?:%s)|(?:%s))*\s*\}' % (pattern, prop1, prop2)
    
    matcher = re.compile(pattern)
    reference = re.compile('"href"\s*\:\s*"([^"\\\]*(?:\\\.[^"\\\]*)*)"')
    injector = {re.compile('^\s*\{'): '{1}{2},'}
    target, response = postJSON, authorJSON
    
#    matcher = re.compile('(<Author\s+href\=\"[^\"]+\")>\s*<Id>[^<]+</Id>\s*(</Author>)')
#    reference = re.compile('href\=\"([^\"]+)\"')
#    injector = {re.compile('^\s*<Collaborator'): '{1}', re.compile('</Collaborator>\s*$'): '{2}'}
#    target, response = postXML, authorXML
    
#    matcher = re.compile('((?:\n|^)Author\:)\n[ \t]+Id\:.*(\n[ \t]+href\:.*)\n')
#    reference = re.compile('\n[ \t]+href\:(.*)')
#    injector = {re.compile('^'): '{1}{2}', re.compile('\n'): '\n  ', re.compile('\n$'): ''}
#    target, response = postYAML, authorYAML
   
    assembled, current = [], 0
    for match in matcher.finditer(target):
        block = match.group()
        assembled.append(target[current:match.start()])
        current = match.end()
        print('1: Identify ' + '-' * 50)
        print(block)
        
        references = reference.findall(block)
        if references: href = references[0]
        else: href = None
        print('2: Get reference ' + '-' * 50)
        print(href)
        
        injected = response
        for replacer, value in injector.items():
            for k, group in enumerate(match.groups()):
                value = value.replace('{%s}' % (k + 1), group)
            injected = replacer.sub(value, injected)
        print('3: Prepare response ' + '-' * 50)
        print(injected)
        
        assembled.append(injected)
    assembled.append(target[current:])

    print('==' * 50)
    print(''.join(assembled))

#    a = '''
#    href: "12\\"34"
#    name: ""
#    '''
#    
#    match = re.compile('"[^"\\\]*(?:\\\.[^"\\\]*)*"')
#    print(a)
#    print(match.findall(a))

#    a = '''a: href, name'''
#    
#    match = re.compile('(a\:(?:(?:\s*href\,?)|(?:\s*name\,?))*)')
#    print(a)
#    print(match.findall(a))

#TODO: convince the XML generator to use only "