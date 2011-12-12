# -*- coding: utf-8 -*-
'''
Created on Sep 9, 2010
@author: Zsolt Török

Copyright (C) 2010 Zsolt Török
 
This file is part of XBMC SoundCloud Plugin.

XBMC SoundCloud Plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

XBMC SoundCloud Plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with XBMC SoundCloud Plugin.  If not, see <http://www.gnu.org/licenses/>.
'''
import httplib2
import urllib
import simplejson as json
import re
import mechanize
import urlparse

# SoundCloud application consumer key.
CONSUMER_KEY = "91c61ef4dbc96933eff93325b5d5183e"
CLIENT_ID_VALUE = CONSUMER_KEY
CLIENT_SECRET_VALUE = "7d782a25f125696162a05f03d1a2df23"
REDURI = "http://www.google.be"

GRANT_TYPE_PASSWORD_VALUE = u'password'
GRANT_TYPE_REFRESH_TOKEN_VALUE = u'refresh_token'
CLIENT_ID_KEY = u'client_id'
CLIENT_SECRET_KEY = u'client_secret'
GRANT_TYPE_KEY = u'grant_type'
SCOPE = u'scope'
NONE_EXPIRY = "non-expiring"
USERNAME_KEY = u'username'
PASSWORD_KEY = u'password'
RESPONSETYPE = u'response_type'
TOKEN = "token"
REDIRECTURI = u'redirect_uri'
DISPLAY = u'display'
POPUP = "popup"

# SoundCloud constants
USER_AVATAR_URL = 'avatar_url'
USER_PERMALINK = 'permalink'
USER_ID = 'id'
USER_NAME = 'username'
USER_PERMALINK_URL = 'permalink_url'
TRACK_USER = 'user'
TRACK_TITLE = 'title'
TRACK_ARTWORK_URL = 'artwork_url'
TRACK_WAVEFORM_URL = 'waveform_url'
TRACK_STREAM_URL = 'stream_url'
TRACK_STREAMABLE = 'streamable'
TRACK_GENRE = 'genre'
TRACK_ID = 'id'
TRACK_PERMALINK = 'permalink'
GROUP_ARTWORK_URL = 'artwork_url'
GROUP_NAME = 'name'
GROUP_ID = 'id'
GROUP_CREATOR = 'creator'
GROUP_PERMALINK_URL = 'permalink_url'
GROUP_PERMALINK = 'permalink'
QUERY_CONSUMER_KEY = 'consumer_key'
QUERY_FILTER = 'filter'
QUERY_OFFSET = 'offset'
QUERY_LIMIT = 'limit'
QUERY_Q = 'q'
QUERY_ORDER = 'order'
QUERY_OAUTH_TOKEN = 'oauth_token'
QUERY_CURSOR = 'cursor'

class SoundCloudClient(object):
    ''' SoundCloud client to handle all communication with the SoundCloud REST API. '''

    def __init__(self, login=False, username='', password='', oauth_token=''):
        '''
        Constructor
        '''
        self.login = login
        self.username = username
        self.password = password
        if login:
            if oauth_token:
                self.oauth_token = oauth_token
                #self.oauth_refresh_token = oauth_refresh_token
            else:
                self.oauth_token = self.get_oauth_tokens()
        
    def get_oauth_tokens_user_credentials_flow(self):
        #not working !!!
        ''' Authenticates with SoundCloud using the given credentials and returns an OAuth access token and a refresh token.'''
        url = 'https://soundcloud.com/oauth2/token?' + urllib.urlencode({CLIENT_ID_KEY : CLIENT_ID_VALUE, CLIENT_SECRET_KEY : CLIENT_SECRET_VALUE, GRANT_TYPE_KEY : GRANT_TYPE_PASSWORD_VALUE, USERNAME_KEY : self.username, PASSWORD_KEY : self.password, SCOPE : NONE_EXPIRY})
        print(url)
        
        try:
            json_content = self._https_get_json(url)
            print (json_content)
            oauth_access_token = json_content.get('access_token')
            #oauth_refresh_token = json_content.get('refresh_token')
        except:
            oauth_access_token = ""
        
        return oauth_access_token
    
    def get_oauth_tokens(self):
        
        url = 'https://soundcloud.com/connect?' + urllib.urlencode({CLIENT_ID_KEY : CLIENT_ID_VALUE, CLIENT_SECRET_KEY : CLIENT_SECRET_VALUE, RESPONSETYPE : TOKEN, SCOPE : NONE_EXPIRY, REDIRECTURI: REDURI, DISPLAY: POPUP})
        print(url)
        try:
            oauth_access_token = self.getsoundcloudconnect(url)
        except:
            oauth_access_token = ""
            self.login = False
        return oauth_access_token
    
    def getsoundcloudconnect(self, url):
        br = mechanize.Browser()
        #Browser options
        br.set_handle_equiv(True)
        #br.set_handle_gzip(True)
        br.set_handle_redirect(True)
        br.set_handle_referer(True)
        br.set_handle_robots(False)
        
        # Follows refresh 0 but not hangs on refresh > 0
        br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
        
        # User-Agent (this is cheating, ok?)
        br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
        
        r = br.open(url)
        
        #html = r.read()
        '''
        for f in br.forms():
            print f
        '''
        # Select the first (normal login) form
        br.select_form(nr=1)
        
        # User credentials
        br.form['username'] = self.username
        br.form['password'] = self.password
        
        # Login
        br.submit()

        result = br.geturl()
        qs = dict(urlparse.parse_qs(result))
        #print (qs.get(REDURI + "?#access_token")[0])   
        return  qs.get(REDURI + "?#access_token")[0]
            
    def get_tracks(self, offset, limit, mode, plugin_url, query=""):
        ''' Return a list of tracks from SoundCloud, based on the parameters. '''
        if self.login:
            url = self._build_query_url(base="https://api.soundcloud.com/", resource_type="tracks", parameters={  QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_Q: query, QUERY_ORDER: "hotness"})
        else:
            url = self._build_query_url(base="http://api.soundcloud.com/", resource_type="tracks", parameters={ QUERY_CONSUMER_KEY: CONSUMER_KEY, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_Q: query, QUERY_ORDER: "hotness"})
        return self._get_tracks(url)

    def _get_tracks(self, url):
        if self.login:
            json_content = self._https_get_json(url)
        else:
            json_content = self._http_get_json(url)
        tracks = []
        for json_entry in json_content:
            if TRACK_ARTWORK_URL in json_entry and json_entry[TRACK_ARTWORK_URL]:
                thumbnail_url = json_entry[TRACK_ARTWORK_URL]
            else:
                thumbnail_url = json_entry[TRACK_USER].get(USER_AVATAR_URL)
            tracks.append({ TRACK_TITLE: json_entry[TRACK_TITLE], TRACK_STREAM_URL: json_entry.get(TRACK_STREAM_URL, ""), TRACK_ARTWORK_URL: thumbnail_url, TRACK_PERMALINK: json_entry[TRACK_PERMALINK], TRACK_ID: json_entry[TRACK_ID] })

        return tracks
    
    def _get_activities_tracks(self, url):
        json_content = self._https_get_json(url)
       
        tracks = []
        for json_entry in json_content["collection"]:
            try:
                track_entry = json_entry["origin"]
                if TRACK_ARTWORK_URL in track_entry and track_entry[TRACK_ARTWORK_URL]:
                    thumbnail_url = track_entry[TRACK_ARTWORK_URL]
                else:
                    thumbnail_url = track_entry[TRACK_USER].get(USER_AVATAR_URL)
                tracks.append({ TRACK_TITLE: track_entry[TRACK_TITLE], TRACK_STREAM_URL: track_entry.get(TRACK_STREAM_URL, ""), TRACK_ARTWORK_URL: thumbnail_url, TRACK_PERMALINK: track_entry[TRACK_PERMALINK], TRACK_ID: track_entry[TRACK_ID] })
            except:
                print(track_entry)
#                tracks = []
                
        try:
            qs = dict(urlparse.parse_qs(urlparse.urlparse(json_content["next_href"]).query))
            nexturl = qs.get(QUERY_CURSOR)[0]
        except:
            nexturl = ""
            
        return tracks,nexturl

    def get_track(self, permalink):
        ''' Return a track from SoundCloud based on the permalink. '''
        if self.login:
            url = self._build_track_query_url(permalink, base='https://api.soundcloud.com/', parameters={QUERY_OAUTH_TOKEN: self.oauth_token})
            print ("track query url: " + url)
            json_content = self._https_get_json(url)
        else:
            url = self._build_track_query_url(permalink, base='http://api.soundcloud.com/', parameters={QUERY_CONSUMER_KEY: CONSUMER_KEY})
            print ("track query url: " + url)
            json_content = self._http_get_json(url)
        #json_content = ""
        print ("track query response JSON: " + str(json_content))
        if TRACK_ARTWORK_URL in json_content and json_content[TRACK_ARTWORK_URL]:
                thumbnail_url = json_content[TRACK_ARTWORK_URL]
        else:
                thumbnail_url = json_content[TRACK_USER].get(USER_AVATAR_URL)
        if self.login:
            track_stream_url_with_consumer_key = '%s?%s' % (json_content[TRACK_STREAM_URL], str(urllib.urlencode({QUERY_OAUTH_TOKEN: self.oauth_token})))
        else:
            track_stream_url_with_consumer_key = '%s?%s' % (json_content[TRACK_STREAM_URL], str(urllib.urlencode({QUERY_CONSUMER_KEY: CONSUMER_KEY})))
        return { TRACK_STREAM_URL: track_stream_url_with_consumer_key, TRACK_TITLE: json_content[TRACK_TITLE], TRACK_ARTWORK_URL: thumbnail_url, TRACK_GENRE: json_content[TRACK_GENRE] }

    def get_group_tracks(self, offset, limit, mode, plugin_url, group_id):
        ''' Return a list of tracks belonging to the given group, based on the specified parameters. '''
        if self.login:
            url = self._build_groups_query_url(base='https://api.soundcloud.com/', resource_type="tracks", group_id=group_id, parameters={ QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        else:
            url = self._build_groups_query_url(base='http://api.soundcloud.com/', resource_type="tracks", group_id=group_id, parameters={ QUERY_CONSUMER_KEY: CONSUMER_KEY, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        return self._get_tracks(url)

    def get_user_tracks(self, offset, limit, mode, plugin_url, user_permalink):
        ''' Return a list of tracks uploaded by the given user, based on the specified parameters. '''
        if self.login:
            url = self._build_users_query_url(base='https://api.soundcloud.com/',resource_type="tracks", user_permalink=user_permalink, parameters={ QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        else:
            url = self._build_users_query_url(base='http://api.soundcloud.com/', resource_type="tracks", user_permalink=user_permalink, parameters={ QUERY_CONSUMER_KEY: CONSUMER_KEY, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        return self._get_tracks(url)
    
    def get_favorite_tracks(self, offset, limit, mode, plugin_url):
        ''' Return a list of tracks favorited by the current user, based on the specified parameters.  login only'''
        url = self._build_query_url(base='https://api.soundcloud.com/', resource_type="me/favorites", parameters={ QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        return self._get_tracks(url)
   
    def get_dash_tracks(self, limit, mode, plugin_url, cursor):
        ''' Return a list of new tracks by the following users of the current user, based on the specified parameters.  login only'''
        if cursor == "":
            url = self._build_query_url(base='https://api.soundcloud.com/', resource_type="me/activities/tracks/affiliated", parameters={ QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_LIMIT: limit})
        else:
            url = self._build_query_url(base='https://api.soundcloud.com/', resource_type="me/activities/tracks/affiliated", parameters={ QUERY_CURSOR: cursor, QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_LIMIT: limit})
        return self._get_activities_tracks(url)
    
    def get_private_tracks(self, limit, mode, plugin_url, cursor):
        ''' Return a list of tracks privately shared to the current user, based on the specified parameters.  login only'''
        if cursor == "":
            url = self._build_query_url(base='https://api.soundcloud.com/', resource_type="me/activities/tracks/exclusive", parameters={ QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_LIMIT: limit})
        else:
            url = self._build_query_url(base='https://api.soundcloud.com/', resource_type="me/activities/tracks/exclusive", parameters={ QUERY_CURSOR: cursor, QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_LIMIT: limit})
        return self._get_activities_tracks(url)
    
    def get_following_groups(self, offset, limit, mode, plugin_url):
        url = self._build_query_url(base='https://api.soundcloud.com/', resource_type="me/groups", parameters={ QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        print(url)
        json_content = self._https_get_json(url)
        return self.get_groups(json_content)

    def get_normal_groups(self, offset, limit, mode, plugin_url, query=""):
        ''' Return a list of groups, based on the specified parameters. '''
        if self.login:
            url = self._build_query_url(base='https://api.soundcloud.com/', resource_type="groups", parameters={ QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
            print(url)
            json_content = self._https_get_json(url)
        else:
            url = self._build_query_url(base='http://api.soundcloud.com/', resource_type="groups", parameters={ QUERY_CONSUMER_KEY: CONSUMER_KEY, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
            print(url)
            json_content = self._http_get_json(url)
        return self.get_groups(json_content)
            
    def get_groups(self, json_content):        
        groups = []
        for json_entry in json_content:
            if GROUP_ARTWORK_URL in json_entry and json_entry[GROUP_ARTWORK_URL]:
                thumbnail_url = json_entry[GROUP_ARTWORK_URL]
            elif GROUP_CREATOR in json_entry and json_entry[GROUP_CREATOR] and USER_AVATAR_URL in json_entry[GROUP_CREATOR] and json_entry[GROUP_CREATOR][USER_AVATAR_URL]:
                thumbnail_url = json_entry[GROUP_CREATOR][USER_AVATAR_URL]
            else:
                thumbnail_url = ""
            groups.append({ GROUP_NAME: json_entry[GROUP_NAME], GROUP_ARTWORK_URL: thumbnail_url, GROUP_ID: json_entry[GROUP_ID], GROUP_PERMALINK_URL: json_entry[GROUP_PERMALINK_URL], GROUP_PERMALINK: json_entry[GROUP_PERMALINK] })

        return groups

    def get_users(self, offset, limit, mode, plugin_url, query):
        if self.login:
            url = self._build_query_url(base='https://api.soundcloud.com/', resource_type="users", parameters={ QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_Q: query, QUERY_ORDER: "hotness"})
        else:
            url = self._build_query_url(base='http://api.soundcloud.com/', resource_type="users", parameters={ QUERY_CONSUMER_KEY: CONSUMER_KEY, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_Q: query, QUERY_ORDER: "hotness"})
        return self._get_users(url)

    def get_following_users(self, offset, limit, mode, plugin_url):
        url = self._build_query_url(base="https://api.soundcloud.com/", resource_type="me/followings", parameters={ QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        return self._get_users(url)
        
    def get_follower_users(self, offset, limit, mode, plugin_url):
        url = self._build_query_url(base="https://api.soundcloud.com/", resource_type="me/followers", parameters={ QUERY_OAUTH_TOKEN : self.oauth_token, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        return self._get_users(url)

    def _get_users(self, url):
        ''' Return a list of users, based on the specified parameters. '''
        if self.login:
            json_content = self._https_get_json(url)
        else:
            json_content = self._http_get_json(url)
        users = []
        for json_entry in json_content:
            users.append({ USER_NAME: json_entry[USER_NAME], USER_AVATAR_URL: json_entry[USER_AVATAR_URL], USER_ID: json_entry[USER_ID], USER_PERMALINK_URL: json_entry[USER_PERMALINK_URL], USER_PERMALINK: json_entry[USER_PERMALINK] })

        return users

    
    def _build_query_url(self, resource_type, parameters, base="https://api.soundcloud.com/", format="json"):
        url = '%s%s.%s?%s' % (base, resource_type, format, str(urllib.urlencode(parameters)))
        print (url)
        return url

    def _build_track_query_url(self, permalink, parameters, base="https://api.soundcloud.com/", format="json"):
        url = '%stracks/%s.%s?%s' % (base, permalink, format, str(urllib.urlencode(parameters)))
        return url

    def _build_groups_query_url(self, group_id, resource_type, parameters, base="https://api.soundcloud.com/", format="json"):
        url = '%sgroups/%d/%s.%s?%s' % (base, group_id, resource_type, format, str(urllib.urlencode(parameters)))
        return url

    def _build_users_query_url(self, user_permalink, resource_type, parameters, base="https://api.soundcloud.com/", format="json"):
        url = '%susers/%s/%s.%s?%s' % (base, user_permalink, resource_type, format, str(urllib.urlencode(parameters)))
        return url
    
    def _http_get_json(self, url):
        h = httplib2.Http()
        resp, content = h.request(url, 'GET')
        if resp.status == 401:
            raise RuntimeError('Authentication error')
        
        return json.loads(content)


    def _https_get_json(self, url):
        #login only
        h = httplib2.Http(disable_ssl_certificate_validation=True)
        resp, content = h.request(url, 'GET')
        if resp.status == 401:
            raise RuntimeError('Authentication error')
        
        return json.loads(content)