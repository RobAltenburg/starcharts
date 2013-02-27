#!/usr/bin/python
import math                                             

class SVG_Chart:
	""" Make SVG Charts """
	
	look_ra = 0	# hours
	look_dec = 0	# degrees
	look_fov = 20	# degrees
	scale_factor = 100 #scales the projection
	cos_dec = 0
	sin_dec = 0
	ramax = 0	# maximum extent of fov on a scale of +/- 1
	decmax = 0      # ditto
	deg_radius = 0

	def __init__(self, ra=0, dec=0, fov=20):
		self.look_ra = ra
		self.look_dec = dec
		self.look_fov = fov
		self.cos_dec = math.cos(math.radians(dec))
		self.sin_dec = math.sin(math.radians(dec))
		
		fov_y = (fov/6.5) * 9.0  # extend fov in y access because map isn't square
		
		center = self.stereographic_projection((ra,dec))
		self.ramax = self.stereographic_projection((ra + ((fov * 0.5)/15.0), dec))[0] 
		self.decmax = self.stereographic_projection((ra, dec + (fov_y * 0.5)))[1]
		self.deg_radius = self.stereographic_projection((ra + 0.5, dec))[0] 

		print "maxvars: " + str((self.ramax,self.decmax))

	#telrad 0.5, 2, 4	

	#-------------------- Projections  --------------------

	def radec_to_tuple (self, radec):
		"Convert a radec string like 'hhmmss.s+ddmmss' to ra and dec"
		# seconds can be of any length, everything else is 2 characters each
		ra = 0
		dec = 0
		if "+" in radec:
			rdt = radec.partition("+")
		elif "-" in radec:
			rdt = radec.partition("-")
		else:
			#todo: catch an error here
			rdt = (0,0,0)
		ra = float(rdt[0][0:2])+(float(rdt[0][2:4])/60.0)+(float(rdt[0][4:])/3600.0)
		dec = float(rdt[2][0:2])+(float(rdt[2][2:4])/60.0)+(float(rdt[2][4:])/3600.0)
		if rdt[1]=="-":
			dec = dec * -1.0
		return ((ra,dec))
		
	# http://mathworld.wolfram.com/StereographicProjection.html

	def scaled_projection (self, xy):
		pxy = self.stereographic_projection(xy)
		x = 3.25 + ((pxy[0]/self.ramax) * 3.25)
		y = 4.5 + ((pxy[1]/self.decmax) * 4.5)
		return ((x,y))

	def stereographic_projection (self, dat):
		delta_ra_rad = math.radians(15*(dat[0] - self.look_ra))
		rdec = math.radians(dat[1])
		x = math.cos(rdec) * math.sin(delta_ra_rad) 
		y = ((self.cos_dec * math.sin(rdec)) - (self.sin_dec * math.cos(rdec) * math.cos(delta_ra_rad))) 
		return ((x,y))		

	def dec_polyline(self, dec):
		ra_start = (self.look_ra) - ((self.look_fov * 0.5)/ 15.0)
		ra_end = (self.look_ra * 15.0) + ((self.look_fov * 0.5)/15.0)
		polyline = ""
		counter = 0
		ra = ra_start
		while ra < ra_end:
			dat = self.scaled_projection((ra,dec))
			polyline = polyline + " %3.2f,%3.2f"%dat
			#" " + str(dat[0]) + "in," + str(dat[1]) + "in"
			ra += 0.01
			counter +=1
		if counter & 1 and True or False:
			polyline = polyline + " %3.2f,%3.2f"%dat
			
		return polyline.strip()



	#-------------------- SVG Routines --------------------
	def draw_borders (self, fileref):
		fileref.write('<rect width="6.5" height="9" fill="white" stroke="black" stroke-width=".025"/>\n')
		#fileref.write('<rect y="7in" width="6.5in" height="2in" fill="grey" stroke="black" stroke-width="2"/>\n')

	def draw_declines (self, fileref):
		fileref.write('<polyline points="' + self.dec_polyline(0)
					  + '" style="fill:none;stroke:blue;stroke-width:.005" />')
		
	def draw_star (self, fileref, radec, mag):
		dat = self.radec_to_tuple(radec)
		xy = self.scaled_projection(dat)
		#todo: better mag scaling function
		rad = (5 - mag) * .01
		if rad <= 0:
			rad = .01
		fileref.write('<circle cx="' + str(xy[0]) + '" cy="' + str(xy[1]) + '" r="' + str(rad) + '"\n'
					  'style="fill:black;stroke:black;stroke-width:.01" />\n')

	def open_chart (self, filename):
		f = open(filename, "w")
		f.write('<svg width="6.5in" height="9in"\n' +
			'viewBox="0 0 6.5 9"\n' +	
			'version="1.1" baseProfile="full"\n' + 
			'xmlns="http://www.w3.org/2000/svg"\n' +
			'xmlns:xlink="http://www.w3.org/1999/xlink"\n' +
			'xmlns:ev="http://www.w3.org/2001/xml-events">\n')
		self.draw_borders(f)
		
		return f
	
	def close_chart(self, fileref):
		fileref.write('</svg>\n')
		fileref.close

	def render (self, filename):
		f = self.open_chart(filename)
		self.draw_star (f, "000100.0+000100", 5)
		self.draw_declines(f)
		self.close_chart(f)

	#-------------------------------------

myChart = SVG_Chart()

myChart.render("test.svg")

dat = myChart.radec_to_tuple("000100.0+000100")
dpr = myChart.scaled_projection(dat)
print "radec ->" + str(dat)
print "proj ->" + str(dpr)
#print "scale ->" + str(myChart.scale_projection(dpr))
#print myChart.dec_polyline(10)
