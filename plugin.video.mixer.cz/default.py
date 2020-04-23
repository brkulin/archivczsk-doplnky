# -*- coding: UTF-8 -*-
# /*
# *      Copyright (C) 2011 Libor Zoubek
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

sys.path.append(os.path.join (os.path.dirname(__file__), 'resources', 'lib'))

import util, xbmcprovider, xbmcutil, resolver
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
import mixercz

__scriptid__ = 'plugin.video.mixer.cz'
__scriptname__ = 'mixer.cz'
__addon__ = ArchivCZSK.get_xbmc_addon(__scriptid__)
__language__ = __addon__.getLocalizedString

settings = {'quality':__addon__.getSetting('quality')}

class MixerczXBMCContentProvider(xbmcprovider.XBMCMultiResolverContentProvider):
    
    def play(self, params):
        stream = self.resolve(params['play'])
        if type(stream) == type([]):
            sdict = {}
            for s in stream:
                if s['surl'] not in sdict:
                    sdict[s['surl']] = s
                if len(sdict) > 1:
                    break
            else:
                return xbmcprovider.XBMCMultiResolverContentProvider.play(self, params)
                
            # resolved to mutliple files, we'll feed playlist and play the first one
            playlist = []
            i = 0
            for video in stream:
                i += 1
                if 'headers' in video.keys():
                    playlist.append(xbmcutil.create_play_it(video['title'] + " [" + str(i) + "]", "", video['quality'], video['url'], subs=video['subs'], filename=params['title'], headers=video['headers']))
                else:
                    playlist.append(xbmcutil.create_play_it(video['title'] + " [" + str(i) + "]", "", video['quality'], video['url'], subs=video['subs'], filename=params['title']))
            xbmcutil.add_playlist(params['title'], playlist)
        elif stream:
            if 'headers' in stream.keys():
                xbmcutil.add_play(params['title'], "", stream['quality'], stream['url'], subs=stream['subs'], filename=params['title'], headers=stream['headers'])
            else:
                xbmcutil.add_play(params['title'], "", stream['quality'], stream['url'], subs=stream['subs'], filename=params['title'])

    def resolve(self, url):
        def select_cb(resolved):
            stream_parts = []
            stream_parts_dict = {}
            
            for stream in resolved:
                if stream['surl'] not in stream_parts_dict:
                    stream_parts_dict[stream['surl']] = []
                    stream_parts.append(stream['surl'])
                stream_parts_dict[stream['surl']].append(stream)

            if len(stream_parts) == 1:
                quality = self.settings['quality'] or '0'
                resolved = resolver.filter_by_quality(stream_parts_dict[stream_parts[0]], quality)
                # if user requested something but 'ask me' or filtered result is exactly 1
                if len(resolved) == 1 or int(quality) > 0:
                    return resolved[0]
                return resolved
            # requested to play all streams in given order - so return them all
            return [stream_parts_dict[p][0] for p in stream_parts]

        item = self.provider.video_item()
        item.update({'url':url})
        return self.provider.resolve(item, select_cb=select_cb)

MixerczXBMCContentProvider(mixercz.MixerczContentProvider(tmp_dir=__addon__.getAddonInfo('profile')), settings, __addon__, session).run(params)
