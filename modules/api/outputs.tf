output "status_table_name" {
  value = aws_dynamodb_table.ascii_art.name
}

output "status_table_arn" {
  value = aws_dynamodb_table.ascii_art.arn
}
