#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>

#include <cassert>
#include <chrono>
#include <filesystem>
#include <iostream>
#include <memory>
#include <random>
#include <thread>

int main(int argc, char **argv) {
  if (argc != 6) {
    std::cerr << "Usage: " << argv[0]
              << ": test-time(s) write-file write(B/s) read-file read(B/s)\n";
    return 1;
  }
  constexpr size_t read_bs = 16 * 1024;
  constexpr size_t write_bs = 1024 * 1024;

  double test_time_sec = std::stod(argv[1]);
  const char *write_file = argv[2];
  double write_bytes_per_sec = std::stod(argv[3]);
  const char *read_file = argv[4];
  double read_bytes_per_sec = std::stod(argv[5]);

  int fd_write = open(write_file, O_CREAT | O_TRUNC | O_WRONLY | O_DIRECT,
                      S_IRUSR | S_IWUSR);
  if (fd_write == -1) {
    perror("open write-file");
    return 1;
  }
  double write_block_per_sec = write_bytes_per_sec / write_bs;
  uint64_t write_interval_ns(1e9 / write_block_per_sec);
  std::chrono::nanoseconds write_interval(write_interval_ns);

  int fd_read = open(read_file, O_RDONLY | O_DIRECT);
  if (fd_read == -1) {
    perror("open read-file");
    return 1;
  }
  double read_block_per_sec = read_bytes_per_sec / read_bs;
  uint64_t read_interval_ns(1e9 / read_block_per_sec);
  std::chrono::nanoseconds read_interval(read_interval_ns);

  struct stat file_stat;
  if (fstat(fd_write, &file_stat) == -1) {
    perror("fstat");
    return 1;
  }
  auto write_align = file_stat.st_blksize;
  auto write_buf_size = write_bs + write_align - 1;
  char write_buf_stack[write_buf_size];
  void *write_buf_alloc = write_buf_stack;
  void *write_buf =
      std::align(write_align, write_bs, write_buf_alloc, write_buf_size);

  if (fstat(fd_read, &file_stat) == -1) {
    perror("fstat");
    return 1;
  }
  auto read_align = file_stat.st_blksize;
  auto read_buf_size = read_bs + read_align - 1;
  char read_buf_stack[read_buf_size];
  void *read_buf_alloc = read_buf_stack;
  void *read_buf =
      std::align(read_align, read_bs, read_buf_alloc, read_buf_size);

  auto num_blocks = file_stat.st_size / read_bs;
  std::uniform_int_distribution<uint64_t> block_dist(0, num_blocks - 1);
  std::random_device rd;
  std::minstd_rand rng(rd());

  std::chrono::nanoseconds read_ns(0);
  uint64_t read_count = 0;
  std::chrono::nanoseconds write_ns(0);
  uint64_t write_count = 0;

  auto start = std::chrono::steady_clock::now();
  auto now = start;
  auto next_write = start + write_interval;
  auto next_read = start + read_interval;
  uint64_t test_time_nsec = test_time_sec * 1e9;
  auto end = start + std::chrono::nanoseconds(test_time_nsec);
  while (now < end) {
    bool do_write;
    std::chrono::time_point<std::chrono::steady_clock> next;
    if (next_write < next_read) {
      do_write = true;
      next = next_write;
      next_write += write_interval;
    } else {
      do_write = false;
      next = next_read;
      next_read += read_interval;
    }
    if (next > now) {
      std::this_thread::sleep_for(next - now);
    }
    auto op_start = std::chrono::steady_clock::now();
    if (do_write) {
      char *buf = (char *)write_buf;
      size_t n = write_bs;
      do {
        ssize_t ret = write(fd_write, buf, n);
        if (ret == -1) {
          perror("write");
          return 1;
        }
        assert(ret > 0);
        n -= ret;
        buf += ret;
      } while (n > 0);
    } else {
      uint64_t offset = block_dist(rng) * read_bs;
      char *buf = (char *)read_buf;
      size_t n = read_bs;
      do {
        ssize_t ret = pread(fd_read, buf, n, offset);
        if (ret == -1) {
          perror("pread");
          return 1;
        }
        assert(ret > 0);
        n -= ret;
        buf += ret;
        offset += ret;
      } while (n > 0);
    }
    now = std::chrono::steady_clock::now();
    auto time = now - op_start;
    if (do_write) {
      write_ns += time;
      write_count += 1;
    } else {
      read_ns += time;
      read_count += 1;
    }
  }
  std::cout << "Write throughput: "
            << write_count * write_bs / test_time_sec / 1e6 << " MB/s\n"
            << "Read throughput: " << read_count * read_bs / test_time_sec / 1e6
            << " MB/s\n"
            << "Averate read latency: " << read_ns.count() / read_count
            << " ns\n";

  return 0;
}
