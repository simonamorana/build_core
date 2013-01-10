# Copyright 2010 - 2013, Qualcomm Innovation Center, Inc.
# 
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
# 
#        http://www.apache.org/licenses/LICENSE-2.0
# 
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
# 

import os
import os.path
import re
import string
from datetime import datetime

import SCons.Builder
from SCons.Node.FS import _my_normcase
from SCons.Tool.JavaCommon import parse_java_file
  
_re_package = re.compile(r'^\s*package\s+([A-Za-z\.]+)', re.M)
_re_public = re.compile(r'^public', re.M)

def parse_javadoc_file(fn):
   """
   Return the package name of Java files with a public class.  As
   configured here, javadoc only generates documentation for public
   classes.
   """
   contents = open(fn, 'r').read()
   pkg = _re_package.search(contents).group(1)
   if _re_public.search(contents):
      return pkg

def javadoc_emitter(source, target, env):
   """
   Look in the source directory for all .java and .html files.  Only
   those .java files with public classes will be listed as a source
   dependency.

   The target is a single file: DOCS/index.html (always generated by
   javadoc).  I could not figure out how to get SCons to use a
   directory as a target, therefore the use of the pseudo-builder
   JavaDoc (and also to handle clean correctly).
   """
   slist = []
   for entry in source:
      def visit(sl, dirname, names):
         d = env.Dir(dirname)
         for fn in names:
            if os.path.splitext(fn)[1] in ['.java']:
               f = d.File(fn)
               f.attributes.javadoc_src = source
               pkg = parse_javadoc_file(str(f))
               if pkg:
                  f.attributes.javadoc_pkg = pkg
                  slist.append(f)
            elif os.path.splitext(fn)[1] in ['.html']:
               f = d.File(fn)
               f.attributes.javadoc_src = source
               if os.path.basename(str(f)) == 'overview.html':
                  f.attributes.javadoc_overview = env.File(str(f)).abspath
               slist.append(f)
      os.path.walk(entry.abspath, visit, slist)
   slist = env.Flatten(slist)

   tlist = [target[0].File('index.html')]

   return tlist, slist

def javadoc_generator(source, target, env, for_signature):
   javadoc_classpath = '-classpath %s' % (env['JAVACLASSPATH'])
   javadoc_windowtitle = '-windowtitle \"%s\"' % (env['PROJECT_LONG_NAME'])
   javadoc_doctitle = '-doctitle \"%s<br/><h3>%s</h3>\"' % (env['PROJECT_LONG_NAME'], env['PROJECT_NUMBER'])
   javadoc_header = '-header \"<b>%s</b>\"' % (env['PROJECT_SHORT_NAME'])
   javadoc_bottom = '-bottom \"' + "<small>%s %s ($(%s$))<br/>Copyright &copy; 2010-2013 Qualcomm Innovation Center, Inc.<br/>This document is licensed under a Creative Commons Attribution-Share Alike 3.0 Unported License; provided,<br/>that (i) any source code incorporated in this document is licensed under the Apache License version 2.0<br/>and (ii) <b>THIS DOCUMENT AND ALL INFORMATION CONTAIN HEREIN ARE PROVIDED ON AN \"AS-IS\" BASIS WITHOUT WARRANTY OF ANY KIND</b>.<br/><a href='http://creativecommons.org/licenses/by-sa/3.0'>Creative Commons Attribution-Share Alike 3.0 Unported License</a><br/><b>MAY CONTAIN U.S. AND INTERNATIONAL EXPORT CONTROLLED INFORMATION</b><br/></small>" % (env['PROJECT_LONG_NAME'], env['PROJECT_NUMBER'], datetime.now().strftime('%a %b %d %H:%M:%S %Y')) + '\"'
   javadoc_overview = ''
   for s in source:
      try:
         javadoc_overview = '-overview ' + s.attributes.javadoc_overview
      except AttributeError:
         pass
   javadoc_packages = []
   for s in source:
      try:
         javadoc_packages.append(s.attributes.javadoc_pkg)
      except AttributeError:
         pass
   javadoc_packages = ' '.join(set(javadoc_packages))
   com = 'javadoc %s -use %s %s -quiet -public -noqualifier all %s %s %s -sourcepath ${SOURCE.srcdir} -d ${TARGET.dir} %s' % (javadoc_classpath, javadoc_windowtitle, javadoc_doctitle, javadoc_header, javadoc_bottom, javadoc_overview, javadoc_packages)
   return com

def JavaDoc(env, target, source, *args, **kw):
   """
   JavaDoc('docs', 'src') will call javadoc on all public .java files
   under the 'src' directory.  Package and private .java files are
   ignored.
   """
   apply(env.JavaDocBuilder, (target, source) + args, kw)
   env.Clean(target, target)
   return [env.Dir(target)]

def generate(env):
   fs = SCons.Node.FS.get_default_fs()
   javadoc_builder = SCons.Builder.Builder(
      generator = javadoc_generator,
      emitter = javadoc_emitter,
      target_factory = fs.Dir,
      source_factory = fs.Dir)
   env.Append(BUILDERS = { 'JavaDocBuilder': javadoc_builder })

   env.AddMethod(JavaDoc, 'JavaDoc')

def exists(env):
   """
   Make sure javadoc exists.
   """
   return env.Detect("javadoc")
