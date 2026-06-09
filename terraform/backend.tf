terraform {
  backend "s3" {
    bucket       = "nba-data-analyst-agent-tfstate-335541954164"
    key          = "nba-data-analyst-agent/terraform.tfstate"
    region       = "ap-northeast-1"
    use_lockfile = true
    encrypt      = true
  }
}