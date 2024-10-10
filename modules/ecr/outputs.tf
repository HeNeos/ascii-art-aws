output "ecr_repo_downsize_media_url" {
  value = aws_ecr_repository.downsize_media.repository_url
}

output "ecr_repo_extract_audio_url" {
  value = aws_ecr_repository.extract_audio.repository_url
}

output "ecr_repo_merge_frames_url" {
  value = aws_ecr_repository.merge_frames.repository_url
}

output "ecr_repo_process_frames_url" {
  value = aws_ecr_repository.process_frames.repository_url
}
