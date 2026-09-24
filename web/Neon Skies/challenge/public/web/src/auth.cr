require "digest/sha256"
require "crypto/subtle"
require "./config"

module NeonSkies
  module Auth
    extend self

    def authenticate(username : String, password : String) : Bool
      user_ok = digest_matches?(username, Config::ADMIN_USER_SHA256)
      pass_ok = digest_matches?(password, Config::ADMIN_PASS_SHA256)

      user_ok & pass_ok
    end

    private def digest_matches?(value : String, expected : String) : Bool
      return false unless expected.size == 64
      Crypto::Subtle.constant_time_compare(Digest::SHA256.hexdigest(value), expected)
    end
  end
end
