#!/usr/bin/env ruby

require 'GTO900'
require 'ast_utils'

dir = ARGV[0]

s = GTO900.new()

s.clear
s.set_center_rate(100)
s.move(dir)
sleep(3)
s.clear
s.halt(dir)
s.close
sleep(2)
