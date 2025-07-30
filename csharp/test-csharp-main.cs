using System;
using System.Data.SqlClient;

class Program {
    static void Main() {
        Console.Write("Enter username: ");
        string username = Console.ReadLine();

        string connectionString = "Server=localhost;Database=TestDB;User Id=sa;Password=Your_password123;";
        string query = "SELECT * FROM Users WHERE Username = '" + username + "'";

        using (SqlConnection connection = new SqlConnection(connectionString)) {
            SqlCommand command = new SqlCommand(query, connection);
            connection.Open();
            SqlDataReader reader = command.ExecuteReader();
            while (reader.Read()) {
                Console.WriteLine(reader["Username"]);
            }
        }
    }
}
