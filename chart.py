#!/usr/bin/python
import math, re                                             

class SVG_Chart:
	""" Make SVG Charts """

	# set the witdh and height in millimeters
	VIEW_WIDTH = 200.0
	VIEW_HEIGHT = 200.0

	mag_limit = 11  		#set the default magnitude limit

	def __init__(self, *args):
		"init takes either the ra, dec, and fov separatly or a radec string and fov"
		# set some global variables
		if len(args) == 3:
			ra = args[0]
			dec = args[1]
			fov = args[2]
		elif len(args) == 2:
			(ra, dec) = self.radec_to_tuple(args[0])
			fov = args[1]
		self.look = (ra,dec,fov)
		self.ramax = self.stereographic_projection((ra + ((fov * 0.5)/15.0), dec))[0] 
		self.decmax = self.ramax # can alter for non-square maps
		self.deg_radius = (self.VIEW_HEIGHT/2) - self.scaled_projection((ra,dec - 1))[1]

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
			#todo: catch an error here for bad formatting of radec string
			print "BAD RADEC: %s"%radec
			return ((0,0))
		ra = (float(rdt[0][0:2])+(float(rdt[0][2:4])/60.0)+(float(rdt[0][4:])/3600.0))%24
		if (len(rdt[2]) > 4):
			dec = float(rdt[2][0:2])+(float(rdt[2][2:4])/60.0)+(float(rdt[2][4:])/3600.0)
		else:
			dec = float(rdt[2][0:2])+float(rdt[2][2:4])/60.0
		if rdt[1]=="-":
			dec = dec * -1.0
		return ((ra,dec))
		
	def scaled_projection (self, xy):
		"scale the projection to the page size"
		#todo: change projection for high dec targets
		pxy = self.stereographic_projection(xy)
		x = (self.VIEW_WIDTH/2.0) + ((pxy[0]/self.ramax) * (self.VIEW_WIDTH/2.0)) 
		y = (self.VIEW_HEIGHT/2.0) + ((pxy[1]/self.decmax) * (self.VIEW_HEIGHT/2.0))
		return ((x,y))

	def stereographic_projection (self, dat):
		"http://mathworld.wolfram.com/StereographicProjection.html"
		cos_dec = math.cos(math.radians(self.look[1]))
		sin_dec = math.sin(math.radians(self.look[1]))
		delta_ra_rad = math.radians(15*(dat[0] - self.look[0]))
		rdec = math.radians(dat[1])
		x = math.cos(rdec) * math.sin(delta_ra_rad) 
		y = ((cos_dec * math.sin(rdec)) - (sin_dec * math.cos(rdec) * math.cos(delta_ra_rad))) 
		return ((x,y))

	def in_look (self, dat):
		"is the angle between look and dat within the field of view."
		pointrarad = math.radians(dat[0] * 15.0)
		pointdecrad = math.radians(dat[1])
		lookdecrad = math.radians(self.look[1])
		deltalon = pointrarad - math.radians(self.look[0] * 15.0)
		diff = math.acos(math.sin(lookdecrad)* math.sin(pointdecrad) + math.cos(lookdecrad)*
				  math.cos(pointdecrad) * math.cos(deltalon))
		if (diff <= math.radians(self.look[2]/2.0)/math.cos(math.pi/4.0)): 
			return True
		else:
			return False
	
	#-------------------- Read data Files --------------------
##	def read_yale (self, filename):
##		retvar = []
##		f = open(filename,"r")
##		lines = f.readlines()
##		data = [(e[0:11],"%3.2f"%(float(e[11:14])/100.0)) for e in lines]
##		for item in data:
##			if len(item[0]) > 5:
##				t = self.radec_to_tuple(item[0])
##				retvar.append((t,float(item[1])))
##		return retvar
##
##	def read_bsc (self, filename):
##		retvar = []
##		f = open(filename,"r")
##		lines = f.readlines()
##		data = [(e[75:90],e[103:107]) for e in lines]
##		for item in data:
##			if len(item[0]) != '               ' and item[1] != '    ':
##				t = self.radec_to_tuple(item[0])
##				retvar.append((t,float(item[1])))
##		return retvar	

	def read_tycho2 (self, filename):
		retvar=[]
		f = open(filename,"r")
		lines = f.readlines()
		data = [e.split('|') for e in lines]
		for item in data:
			m = float(item[2])
			if m <= self.mag_limit:
				t = self.radec_to_tuple(item[0])
				retvar.append((t,float(item[2])))
		return retvar


	def read_gcvs (self, filename):
		retvar = []
		non_decimal = re.compile(r'[^\d.]+')
		f = open(filename,"r")
		lines = f.readlines()
		for item in lines:
			data = item.split('|')
			t = self.radec_to_tuple(data[1])
			#t = data[1]
			if len(data[3]) >= 1:
				m = float(non_decimal.sub('',data[3]))
				retvar.append((t,m))
		return retvar

	#-------------------- SVG Routines --------------------
	def dec_polyline(self, dec):
		"calculate the segment coords for dec lines"
		polyline = ""
		step = self.look[2] / 90.0
		ra = self.look[0] - 12.0
		while ra < self.look[0] + 12.0:
			if self.in_look((ra,dec)) and self.in_look((ra + step,dec)):
				dat1 = self.scaled_projection((ra,dec))
				dat2 = self.scaled_projection((ra + step/15.0,dec))			
				polyline = polyline + "%3.2f,%3.2f %3.2f,%3.2f "%(dat1[0], dat1[1], dat2[0], dat2[1])
			ra += step
		return polyline.strip()

	def ra_polyline(self, ra):
		"calculate the segment coords for ra lines"
		polyline = ""
		dec = -89
		while dec < 89.0:
			if self.in_look((ra,dec)):
				dat1 = self.scaled_projection((ra,dec))
				dat2 = self.scaled_projection((ra + 0.1/15.0,dec))			
				polyline = polyline + "%3.2f,%3.2f %3.2f,%3.2f "%(dat1[0], dat1[1], dat2[0], dat2[1])
			dec += 1		
		return polyline.strip()

	def draw_declines (self):
		self.fileref.write('<!--- Declination Lines --->\n')
		self.fileref.write('<g class="radec_lines">\n')
		lat = -80 
		while lat <= 80: 
			points = self.dec_polyline(lat)
			if len(points) > 0:
				self.fileref.write('<polyline points="' + points + '" />\n')
			lat += 10
		self.fileref.write('</g>\n')
		
	def draw_ralines (self):
		self.fileref.write('<!--- Right Ascension Lines --->\n')
		self.fileref.write('<g class="radec_lines">\n')
		ra = int(self.look[0] - (self.look[0] * 0.5)) 
		while ra <= (self.look[2] * 0.5) + self.look[0]:
			points = self.ra_polyline(ra)
			if len(points) > 0:
				self.fileref.write('<polyline points="' + points + '" />\n')
			ra += 1
		self.fileref.write('</g>\n')			
	
	def draw_star (self, dat, mag):
		if self.in_look(dat):
			xy = self.scaled_projection(dat)
			#todo: better mag scaling function
			dmag = 0.8 * self.mag_limit - mag
			if dmag <= 0:
				rad = 0.1
			else:
				rad = math.log10(dmag) + 0.1
			self.fileref.write('<circle cx="%3.2f" cy="%3.2f" r="%3.2f" />\n'%(xy[0],xy[1],rad))

	def draw_target (self, dat, mag):
		if self.in_look(dat):
			xy = self.scaled_projection(dat)
			self.fileref.write('<line x1="%3.2f" y1="%3.2f" x2="%3.2f" y2="%3.2f" />\n'%(xy[0]-2,xy[1],xy[0]+2,xy[1]))
			self.fileref.write('<line x1="%3.2f" y1="%3.2f" x2="%3.2f" y2="%3.2f" />\n'%(xy[0],xy[1]-2,xy[0],xy[1]+2))
			
	def draw_telrad (self):
		"Draw telrad circles"
		# note: telrad rings are 4, 2, & 0.5 deg in diameter
		self.fileref.write('<!--- Telrad --->\n')
		self.fileref.write('<g style="fill:none;stroke:red;stroke-width:.15">\n')		
		center = self.scaled_projection((self.look[0],self.look[1]))
		self.fileref.write('<circle cx="%3.2f" cy="%3.2f" r="%3.2f" />\n'%(center[0],center[1],self.deg_radius * 2.0))
		self.fileref.write('<circle cx="%3.2f" cy="%3.2f" r="%3.2f" />\n'%(center[0],center[1],self.deg_radius * 1.0))
		self.fileref.write('<circle cx="%3.2f" cy="%3.2f" r="%3.2f" />\n'%(center[0],center[1],self.deg_radius * 0.25))
		self.fileref.write('</g>\n')
		
	def open_chart (self, filename):
		f = open(filename, "w")
		self.fileref = f
		f.write('<!DOCType html>\n<html>\n<body>' +
			'<svg width="%4.1fmm" height="%4.1fmm"\n'%(self.VIEW_WIDTH, self.VIEW_HEIGHT) +				
			'viewBox="0 0 %4.1f %4.1f"\n'%(self.VIEW_WIDTH, self.VIEW_HEIGHT) +	
			'version="1.1" baseProfile="full"\n' + 
			'xmlns="http://www.w3.org/2000/svg"\n' +
			'xmlns:xlink="http://www.w3.org/1999/xlink"\n' +
			'xmlns:ev="http://www.w3.org/2001/xml-events">\n' +
			'<style>\n.radec_lines{fill:none;stroke:blue;stroke-width:.075;stroke-dasharray:1,2}\n' +
			'.stars{fill:black;stroke:black;stroke-width:0.1}\n' +
			'.targets{fill:green;stroke:green;stroke-width:0.2}\n' +
			'</style>\n' +	
			'<g transform="rotate(180,%3.2f,%3.2f)">\n'%((self.VIEW_WIDTH/2.0, self.VIEW_HEIGHT/2.0)))
	
	def close_chart(self):
		self.fileref.write('<!--- Closing --->\n')
		self.fileref.write('<rect width="%4.2f" height="%4.2f" style="fill:none;stroke:black;stroke-width:0.5"/>\n'%(self.VIEW_WIDTH,self.VIEW_HEIGHT))
		self.fileref.write('</g></svg></body><html>\n')
		self.fileref.close()

	def render (self, filename, title):
		self.open_chart(filename)

##		# Plot the variable stars in the field
##		targets = self.read_gcvs("./data/gcvs.dat")
##		self.fileref.write('<!--- Target Objects --->\n')
##		self.fileref.write('<g class="targets">\n')
##		for t in targets:
##			if (t[1] <= self.mag_limit):
##				self.draw_target (t[0],t[1])
##		self.fileref.write('</g>\n')

		if self.look[2] <= 10:
			stars =  self.read_tycho2("./data/tyc2_mag11.dat")
			self.mag_limit = 11
		else:
			stars =  self.read_tycho2("./data/tyc2_mag8.dat")
			self.mag_limit = 8
		self.fileref.write('<!--- Stars --->\n')
		self.fileref.write('<g class="stars">\n')
		for s in stars:
				self.draw_star (s[0],s[1])
		self.fileref.write('</g>\n')

		self.draw_telrad()
		self.draw_declines()
		self.draw_ralines()

		self.fileref.write('<rect width="%4.2f" height="%4.2f" style="fill:white;fill-opacity:0.5;stroke:#202020;stroke-width:.2"/>\n'%(self.VIEW_WIDTH,10))
		self.fileref.write('<!--- Titles --->\n')
		self.fileref.write('<g transform="rotate(180,%3.2f,%3.2f)">\n'%((self.VIEW_WIDTH/2.0, self.VIEW_HEIGHT/2.0)))
		self.fileref.write('<text x=%3.2f y=%3.2f font-family="serif" font-size="5" >\n'%(4,self.VIEW_HEIGHT - 3.0))
		self.fileref.write(title)
		self.fileref.write('</text></g>\n')

		self.close_chart()

#-------------------------------------
#myChart = SVG_Chart(4.5986, 16.5092,90)  	# Aldebaran
#myChart = SVG_Chart(5.5334, 0.2992,90) 		# Mintaka
#myChart = SVG_Chart(18.6156, 38.7837,85) 		# Vega
#myChart = SVG_Chart(10.6156, 48.7837,90) 		

#myChart = SVG_Chart(3.8, 24,30) 			#Pleiades
#myChart.render("test.html", "Pleiades (%2.2f deg field)"%30.0 )

#myChart = SVG_Chart('064107.18+102642.4',45.0)	# SS Mon
#myChart.render("test.html", "SS Mon: 064107.18+102642.4 (%2.2f deg field)"%45.0 )

myChart = SVG_Chart('193043.3+275734.8', 45.0)	# Albireo
myChart.render("test.html", "Albireo: 193043.3+275734.8 (%2.2f deg field)"%45.0 )

#myChart = SVG_Chart('053200.38-001756.8',10) 		# Mintaka
#myChart.render("test.html", "Mintaka (%2.2f deg field)"%10.0 )

#myChart = SVG_Chart('043555+163033',25.0)		# Aldebaran (RaDec version)
#myChart.render("test.html", "Aldebaran: 043555+163033 (%2.2f deg field)"%25.0 )


