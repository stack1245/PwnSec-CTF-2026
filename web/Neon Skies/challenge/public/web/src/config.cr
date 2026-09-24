module NeonSkies
  module Config
    ADMIN_USER_SHA256 = (ENV["ADMIN_USERNAME_SHA256"]? || "").strip.downcase
    ADMIN_PASS_SHA256 = (ENV["ADMIN_PASSWORD_SHA256"]? || "").strip.downcase

    HOST = ENV["HOST"]? || "0.0.0.0"
    PORT = (ENV["PORT"]? || "3000").to_i

    SESSION_COOKIE = "sid"
    SIGNAL_COOKIE  = "FLAG"

    SESSION_TTL = Time::Span.new(hours: 8)
  end
end
