require "http/server"
require "http/cookie"
require "html"

require "./config"
require "./sessions"
require "./auth"
require "./skyline"
require "./views"

module NeonSkies
  extend self

  def cookie_value(request : HTTP::Request, name : String) : String
    request.cookies[name]?.try(&.value) || ""
  rescue
    ""
  end

  def page(*, title : String, active : String, body : String) : String
    Views::Page.new(
      title: title,
      active: active,
      body: body,
      far: Skyline::FAR,
      mid: Skyline::MID,
      near: Skyline::NEAR,
    ).to_s
  end

  def render_html(response : HTTP::Server::Response, body : String, status : HTTP::Status = :ok) : Nil
    response.status = status
    response.content_type = "text/html; charset=utf-8"
    response.print body
  end

  def redirect(response : HTTP::Server::Response, location : String) : Nil
    response.status = :found
    response.headers["Location"] = location
    response.content_type = "text/html; charset=utf-8"
    response.print %(<a href="#{HTML.escape(location)}">continue</a>)
  end

  def issue_session(response : HTTP::Server::Response, sessions : SessionStore, username : String) : String
    id = sessions.create(username)
    response.cookies << HTTP::Cookie.new(
      name: Config::SESSION_COOKIE,
      value: id,
      path: "/",
      expires: Time.utc + Config::SESSION_TTL,
      http_only: true,
      samesite: HTTP::Cookie::SameSite::Lax,
    )
    id
  end

  def run : Nil
    sessions = SessionStore.new

    server = HTTP::Server.new do |context|
      request  = context.request
      response = context.response

      response.headers["X-Content-Type-Options"] = "nosniff"
      response.headers["Referrer-Policy"] = "no-referrer"
      response.headers["X-Frame-Options"] = "DENY"

      sid      = cookie_value(request, Config::SESSION_COOKIE)
      session  = sessions.fetch(sid.empty? ? nil : sid)
      username = session.try(&.username)
      signal   = cookie_value(request, Config::SIGNAL_COOKIE)

      case {request.method, request.path}
      when {"GET", "/"}
        render_html response, page(
          title: "The City Is Still Lit",
          active: "index",
          body: Views::Index.new(username: username).to_s,
        )

      when {"GET", "/login"}
        render_html response, page(
          title: "Access Terminal",
          active: "login",
          body: Views::Login.new(error: nil, username_field: "").to_s,
        )

      when {"POST", "/login"}
        form      = request.form_params
        submitted = form["username"]?.to_s
        password  = form["password"]?.to_s

        if Auth.authenticate(submitted, password)
          issue_session(response, sessions, submitted)
          redirect response, "/admin"
        else
          render_html response, page(
            title: "Access Terminal",
            active: "login",
            body: Views::Login.new(
              error: "Credentials rejected. The vault does not remember you.",
              username_field: submitted,
            ).to_s,
          ), :unauthorized
        end

      when {"POST", "/logout"}, {"GET", "/logout"}
        sessions.destroy(sid.empty? ? nil : sid)
        response.cookies << HTTP::Cookie.new(
          name: Config::SESSION_COOKIE, value: "", path: "/", expires: Time.utc(1970, 1, 1),
        )
        redirect response, "/"

      when {"GET", "/admin"}
        if session.nil?
          redirect response, "/login"
        else
          render_html response, page(
            title: "The Seed Vault",
            active: "admin",
            body: Views::Admin.new(
              flag: signal.empty? ? "" : signal,
              username: session.not_nil!.username,
              session_id: sid,
            ).to_s,
          )
        end

      when {"GET", "/healthz"}
        response.content_type = "text/plain; charset=utf-8"
        response.print "ok"

      else
        render_html response, page(
          title: "Signal Lost",
          active: "404",
          body: Views::NotFound.new(path: request.path).to_s,
        ), :not_found
      end
    end

    puts "[neon_skies] listening on #{Config::HOST}:#{Config::PORT}"
    server.listen(Config::HOST, Config::PORT)
  end
end

NeonSkies.run
