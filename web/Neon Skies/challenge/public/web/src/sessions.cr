require "random/secure"
require "./config"

module NeonSkies
  class SessionStore
    record Entry, username : String, created_at : Time

    @entries = {} of String => Entry
    @mutex   = Mutex.new

    def create(username : String) : String
      id = Random::Secure.hex(32)
      @mutex.synchronize { @entries[id] = Entry.new(username, Time.utc) }
      id
    end

    def fetch(id : String?) : Entry?
      return nil if id.nil? || id.empty?
      @mutex.synchronize do
        entry = @entries[id]?
        if entry && (Time.utc - entry.created_at) > Config::SESSION_TTL
          @entries.delete(id)
          nil
        else
          entry
        end
      end
    end

    def destroy(id : String?) : Nil
      return if id.nil? || id.empty?
      @mutex.synchronize { @entries.delete(id) }
    end

    def size : Int32
      @mutex.synchronize { @entries.size }
    end
  end
end
