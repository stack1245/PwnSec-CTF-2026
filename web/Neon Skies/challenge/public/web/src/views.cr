require "ecr/macros"
require "html"
require "./skyline"

module NeonSkies
  module Views
    STYLESHEET = {{ read_file "public/style.css" }}
    SCRIPT     = {{ read_file "public/app.js" }}

    class Page
      def initialize(*, @title : String, @active : String, @body : String,
                     @far : Array(Building), @mid : Array(Building), @near : Array(Building)); end

      ECR.def_to_s "src/views/layout.ecr"
    end

    class Index
      def initialize(*, @username : String?); end

      ECR.def_to_s "src/views/index.ecr"
    end

    class Login
      def initialize(*, @error : String?, @username_field : String); end

      ECR.def_to_s "src/views/login.ecr"
    end

    class Admin
      def initialize(*, @flag : String, @username : String, @session_id : String); end

      ECR.def_to_s "src/views/admin.ecr"
    end

    class NotFound
      def initialize(*, @path : String); end

      ECR.def_to_s "src/views/notfound.ecr"
    end
  end
end
