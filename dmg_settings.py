# -*- coding: utf-8 -*-
import os
application = 'InfoCenter.app'
volume_name = 'InfoCenter'
format = 'UDZO'
compression_level = 9
files = [f'dist/{application}']
hide_extensions = ['InfoCenter.app']
symlinks = {'Applications': '/Applications'}
volume_icon = 'icon.icns'
icon_locations = {application: (140, 120), "Applications": (500, 120)}

background = "builtin-arrow"

show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False
sidebar_width = 180

window_rect = ((100, 100), (640, 280))
default_view = "icon-view"

include_icon_view_settings = "auto"
include_list_view_settings = "auto"

arrange_by = None
grid_offset = (0, 0)
grid_spacing = 100
scroll_position = (0, 0)
label_pos = "bottom"
text_size = 16
icon_size = 128