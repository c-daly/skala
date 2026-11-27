#include <atomic>
#include <QApplication>
#include <QEvent>
#include <QElapsedTimer>
#include <QKeyEvent>
#include <QLabel>
#include <QPushButton>
#include <QSet>
#include <QSlider>
#include <QTimer>
#include <QVBoxLayout>
#include <rviz_common/panel.hpp>
#include <rviz_common/display_context.hpp>
#include <rviz_common/ros_integration/ros_node_abstraction_iface.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <std_msgs/msg/string.hpp>
#include <pluginlib/class_list_macros.hpp>

namespace skala_rviz_teleop
{
class DrivePanel : public rviz_common::Panel
{
  Q_OBJECT
public:
  explicit DrivePanel(QWidget * parent = nullptr) : rviz_common::Panel(parent)
  {
    auto * layout = new QVBoxLayout(this);
    auto * help = new QLabel("<b>Drive in this map window</b><br>Hold W / S: forward / reverse<br>Hold A / D: turn left / right<br>Release: stop motion<br>Space: stop and disable", this);
    help->setWordWrap(true);
    layout->addWidget(help);
    enable_ = new QPushButton("Enable WASD", this);
    enable_->setObjectName("skala_enable_wasd");
    layout->addWidget(enable_);
    auto * stop_button = new QPushButton("STOP — Space", this);
    stop_button->setObjectName("skala_stop");
    stop_button->setStyleSheet("background: #922f24; color: white; font-weight: bold; padding: 8px;");
    layout->addWidget(stop_button);
    speed_label_ = new QLabel("Speed: 0.15 m/s", this);
    layout->addWidget(speed_label_);
    speed_ = new QSlider(Qt::Horizontal, this);
    speed_->setRange(5, 25); speed_->setValue(15);
    layout->addWidget(speed_);
    status_ = new QLabel("Stopped", this);
    status_->setWordWrap(true);
    layout->addWidget(status_);
    auto * controller_help = new QLabel("Controller: scripts/skala-sim controller<br>Hold LB + left stick; B stops.<br>Keyboard stops when RViz loses focus.", this);
    controller_help->setWordWrap(true);
    layout->addWidget(controller_help);
    layout->addStretch();
    connect(speed_, &QSlider::valueChanged, this, [this](int v) {
      speed_label_->setText(QString("Speed: %1 m/s").arg(v/100.0, 0, 'f', 2));
    });
    connect(enable_, &QPushButton::clicked, this, [this]() {
      if (!mode_pub_ || mode_pub_->get_subscription_count() == 0) {
        status_->setText("Waiting for the simulation command guard"); return;
      }
      keys_.clear(); enabled_ = true; mode_.store(1); enabled_at_.start();
      std_msgs::msg::String mode; mode.data = "keyboard"; mode_pub_->publish(mode);
      enable_->setText("WASD enabled");
    });
    connect(stop_button, &QPushButton::clicked, this, [this]() {stop();});
    timer_ = new QTimer(this);
    timer_->setTimerType(Qt::PreciseTimer);
    connect(timer_, &QTimer::timeout, this, [this]() {tick();});
    timer_->start(50);
    qApp->installEventFilter(this);
  }

  ~DrivePanel() override {qApp->removeEventFilter(this); if (enabled_) stop();}

  void onInitialize() override
  {
    auto node = getDisplayContext()->getRosNodeAbstraction().lock()->get_raw_node();
    velocity_ = node->create_publisher<geometry_msgs::msg::Twist>("/sim/keyboard/cmd_vel", 10);
    mode_pub_ = node->create_publisher<std_msgs::msg::String>("/sim/control_mode", 10);
    subscription_ = node->create_subscription<std_msgs::msg::String>("/sim/control_mode/state", 10,
      [this](std_msgs::msg::String::ConstSharedPtr m) {
        mode_.store(m->data == "keyboard" ? 1 : m->data == "manual" ? 2 : m->data == "demo" ? 3 : 0);
      });
    QTimer::singleShot(1500, this, [this]() {window()->showMaximized();});
  }

protected:
  bool eventFilter(QObject * object, QEvent * event) override
  {
    if (event->type() == QEvent::ApplicationDeactivate ||
        (event->type() == QEvent::WindowDeactivate && object == window())) {
      if (enabled_) {qInfo("Skala keyboard stopped: RViz lost focus"); stop();}
    }
    auto * widget = qobject_cast<QWidget *>(object);
    if (!widget || widget->window() != window()) return false;
    if (event->type() == QEvent::ShortcutOverride || event->type() == QEvent::KeyPress || event->type() == QEvent::KeyRelease) {
      auto * key = static_cast<QKeyEvent *>(event);
      const int k = key->key();
      if (k == Qt::Key_Space || (enabled_ && (k == Qt::Key_W || k == Qt::Key_A || k == Qt::Key_S || k == Qt::Key_D))) {
        if (event->type() == QEvent::ShortcutOverride) {event->accept(); return true;}
        if (key->isAutoRepeat()) return true;
        if (k == Qt::Key_Space && event->type() == QEvent::KeyPress) stop();
        else if (event->type() == QEvent::KeyPress) keys_.insert(k);
        else keys_.remove(k);
        if (enabled_) publish(); // Respond immediately; timer only maintains the lease.
        return true;
      }
    }
    return false;
  }

private:
  void stop()
  {
    enabled_ = false; keys_.clear();
    if (rclcpp::ok() && velocity_ && mode_pub_) {
      velocity_->publish(geometry_msgs::msg::Twist());
      std_msgs::msg::String mode; mode.data = "stopped"; mode_pub_->publish(mode);
    }
    enable_->setText("Enable WASD"); status_->setText("Stopped");
  }
  void publish()
  {
    if (!velocity_ || !rclcpp::ok()) return;
    geometry_msgs::msg::Twist cmd;
    cmd.linear.x = (keys_.contains(Qt::Key_W)-keys_.contains(Qt::Key_S))*speed_->value()/100.0;
    cmd.angular.z = (keys_.contains(Qt::Key_A)-keys_.contains(Qt::Key_D))*.6;
    velocity_->publish(cmd);
    status_->setText(QString("WASD active · %1 m/s · %2 rad/s").arg(cmd.linear.x,0,'f',2).arg(cmd.angular.z,0,'f',2));
  }
  void tick()
  {
    const int mode = mode_.load();
    if (enabled_ && mode != 1 && enabled_at_.elapsed() > 500) {enabled_ = false; keys_.clear(); enable_->setText("Enable WASD");}
    if (enabled_) publish();
    else status_->setText(mode == 2 ? "Controller / browser has control" : mode == 3 ? "Automatic route has control" : "Stopped — click Enable WASD");
  }
  bool enabled_ = false;
  std::atomic<int> mode_{0};
  QSet<int> keys_;
  QElapsedTimer enabled_at_;
  QPushButton * enable_;
  QLabel * status_;
  QLabel * speed_label_;
  QSlider * speed_;
  QTimer * timer_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr velocity_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr mode_pub_;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
};
}
PLUGINLIB_EXPORT_CLASS(skala_rviz_teleop::DrivePanel, rviz_common::Panel)
#include "drive_panel.moc"
