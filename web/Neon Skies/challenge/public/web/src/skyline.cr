module NeonSkies
  struct Building
    getter left : Float64
    getter width : Float64
    getter height : Float64
    getter lit : Float64
    getter spire : Int32
    getter band : Int32
    getter sign : Int32

    def initialize(*, @left, @width, @height, @lit, @spire, @band, @sign); end

    def css_vars : String
      String.build do |s|
        s << "--x:" << left.round(2) << "%;"
        s << "--w:" << width.round(2) << "%;"
        s << "--h:" << height.round(2) << "%;"
        s << "--lit:" << lit.round(3) << ";"
        s << "--band:" << band << ";"
        s << "--spire:" << spire << ";"
        s << "--sign:" << sign << ";"
      end
    end
  end

  module Skyline
    extend self

    FAR  = layer(0x5EED1A7Cu64, min_h: 12.0, max_h: 30.0, min_w: 3.2, max_w: 7.5, sign_odds: 0)
    MID  = layer(0xC0FFEE11u64, min_h: 20.0, max_h: 46.0, min_w: 4.4, max_w: 9.8, sign_odds: 14)
    NEAR = layer(0xD15EA5Eu64, min_h: 30.0, max_h: 68.0, min_w: 5.6, max_w: 13.0, sign_odds: 26)

    def layer(seed : UInt64, *, min_h : Float64, max_h : Float64,
              min_w : Float64, max_w : Float64, sign_odds : Int32) : Array(Building)
      rnd = Random::PCG32.new(seed)
      out = [] of Building
      x = -4.0

      while x < 104.0
        w = min_w + rnd.rand * (max_w - min_w)
        h = min_h + rnd.rand * (max_h - min_h)

        out << Building.new(
          left: x,
          width: w,
          height: h,
          lit: 0.08 + rnd.rand * 0.5,
          spire: rnd.rand(100) < 24 ? 1 + rnd.rand(3).to_i : 0,
          band: rnd.rand(3).to_i,
          sign: sign_odds > 0 && rnd.rand(100).to_i < sign_odds ? 1 + rnd.rand(3).to_i : 0
        )

        x += w + 0.4 + rnd.rand * 1.9
      end

      out
    end
  end
end
