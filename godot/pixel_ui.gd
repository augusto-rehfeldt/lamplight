extends RefCounted

static func icon(kind: String) -> Texture2D:
	var patterns := {
		"book":["01111110","11011011","11011011","11011011","11011011","11011011","11111111","01100110"],
		"map":["11011011","11111111","10111101","10100101","10100101","10111101","11111111","11011011"],
		"ai":["01111110","11000011","10100101","10000001","10111101","11000011","01111110","00100100"],
		"star":["00011000","00011000","11111111","01111110","00111100","01111110","01100110","11000011"],
		"coin":["00111100","01100110","11011011","11010011","11001011","11011011","01100110","00111100"],
		"arrow":["00010000","00011000","11111100","11111110","11111100","00011000","00010000","00000000"]}
	var pixels: Array = patterns.get(kind,patterns.book)
	var bitmap := Image.create(8,8,false,Image.FORMAT_RGBA8)
	bitmap.fill(Color.TRANSPARENT)
	for y in range(8):
		for x in range(8):
			if pixels[y][x] == "1":
				bitmap.set_pixel(x,y,Color("52754b"))
	return ImageTexture.create_from_image(bitmap)
