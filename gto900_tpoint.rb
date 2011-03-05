#!/usr/bin/env ruby

require 'GTO900'
require 'ast_utils'

ra = ARGV[0]
dec = ARGV[1]

ra_deg = 15.0*hms2deg(ra)
dec_deg = hms2deg(dec)

#s = GTO900.new('massdimm', 7001)
#s.clear

lst = 15*hms2deg(s.lst)
h = lst - ra_deg

if h < 0.0
  puts "Pointing East."
  ih = 1087.6/3600.0
  id = 101.2/3600.0
  ch = 221.5/3600.0
  me = 45.3/3600.0
  ma = -261.4/3600.0
  ra_deg = ra_deg + ih + ch/Math::cos(dec_deg*Math::PI/180.0) - ma*Math::cos(h*Math::PI/180.0)*Math::tan(dec_deg*Math::PI/180.0)
  dec_deg = dec_deg + id
else
  puts "Pointing West."
  ih = 1132.0/3600.0
  id = -7.65/3600.0
  ch = -284.9/3600.0
  me = 86.8/3600.0
  ma = -339.1/3600.0
  ra_deg = ra_deg + ih + ch/Math::cos(dec_deg*Math::PI/180.0) - ma*Math::cos(h*Math::PI/180.0)*Math::tan(dec_deg*Math::PI/180.0)
  dec_deg = dec_deg + id - ma*Math::sin(h*Math::PI/180.0)
end

ra = sexagesimal(ra_deg/15.0).sub('+', '') 
dec = sexagesimal(dec_deg)

puts ra + ' ' + dec

rh, rm, rs = ra.split(':')
dd, dm, ds = dec.split(':')

# s.command_ra(rh.to_i, rm.to_i, rs.to_i)
# s.command_dec(dd.to_i, dm.to_i, ds.to_i)
# s.slew

# loop {
#   r = s.ra
#   d = s.dec
#   az = s.az
#   alt = s.alt

#   puts "At RA = %s, Dec = %s, Alt = %s, Az = %s" % [r, d, alt, az]

#   d_ra = 15.0*Math::cos(hms2deg(d)*Math::PI/180.0)*(hms2deg(r) - hms2deg(ra))
#   d_dec = hms2deg(d) - hms2deg(dec)

#   puts "\t %f degrees to go in RA, %f degrees to go in Dec...." % [d_ra, d_dec]
#   if d_ra.abs < 1.0/60.0 && d_dec.abs < 1.0/60.0
#     puts "Done slewing."
#     break
#   end
#   sleep(1)
# }

# s.close